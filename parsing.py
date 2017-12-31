import collections

def consume_newlines(index, tokens):
    while index < len(tokens) and tokens[index].type == 'newline':
        index += 1

    return True, index, None

def _or_parser(*parsers):
    def result_parser(index, tokens):
        failure = (False, index, None)

        for parser in parsers:
            success, index, value = parser(index, tokens)

            if success:
                return (success, index, value)

        return failure

    return result_parser

def _zero_or_more_parser(formatter, parser):
    def result_parser(index, tokens):
        values = []

        while index < len(tokens):
            success, index, value = parser(index, tokens)

            if success:
                values.append(value)
            else:
                break

        return (True, index, formatter(values))

    return result_parser

NodeMetadata = collections.namedtuple(
    'NodeMetadata',
    [
        'index',
        'line',
    ],
)

FurIntegerLiteralExpression = collections.namedtuple(
    'FurIntegerLiteralExpression',
    [
        'integer',
    ],
)

FurStringLiteralExpression = collections.namedtuple(
    'FurStringLiteralExpression',
    [
        'string',
    ],
)

FurSymbolExpression = collections.namedtuple(
    'FurSymbolExpression',
    [
        'metadata',
        'symbol',
    ],
)

FurNegationExpression = collections.namedtuple(
    'FurNegationExpression',
    [
        'metadata',
        'value',
    ],
)

FurInfixExpression = collections.namedtuple(
    'FurInfixExpression',
    [
        'metadata',
        'order',
        'operator',
        'left',
        'right',
    ],
)

FurListLiteralExpression = collections.namedtuple(
    'FurListLiteralExpression',
    [
        'item_expression_list',
    ],
)

FurIfExpression = collections.namedtuple(
    'FurIfExpression',
    [
        'condition_expression',
        'if_statement_list',
        'else_statement_list',
    ],
)

FurSymbolExpressionPair = collections.namedtuple(
    'FurSymbolExpressionPair',
    [
        'symbol',
        'expression',
    ],
)

FurStructureLiteralExpression = collections.namedtuple(
    'FurStructureLiteralExpression',
    [
        'fields',
    ],
)

def _integer_literal_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type != 'integer_literal':
        return failure
    value = int(tokens[index].match)
    index += 1

    return True, index, FurIntegerLiteralExpression(integer=value)

def _string_literal_expression_parser(index, tokens):
    if tokens[index].type == 'double_quoted_string_literal':
        return (True, index + 1, FurStringLiteralExpression(string=tokens[index].match[1:-1]))

    if tokens[index].type == 'single_quoted_string_literal':
        return (True, index + 1, FurStringLiteralExpression(string=tokens[index].match[1:-1]))

    return (False, index, None)

def _symbol_expression_parser(index, tokens):
    if tokens[index].type == 'symbol':
        return (
            True,
            index + 1,
            FurSymbolExpression(
                metadata=NodeMetadata(
                    index=tokens[index].index,
                    line=tokens[index].line,
                ),
                symbol=tokens[index].match,
            ),
        )

    return (False, index, None)

def _wrapped_parser(open_token, close_token, internal_parser):
    def result_parser(index, tokens):
        failure = (False, index, None)

        if tokens[index].type == open_token:
            index += 1
        else:
            return failure

        success, index, internal = internal_parser(index, tokens)
        if not success:
            return failure

        if tokens[index].type == close_token:
            index += 1
        else:
            # TODO Put the actual expected character in the error message
            raise Exception('Expected closing token on line {}, found "{}"'.format(
                tokens[index].line,
                tokens[index].match,
            ))

        return True, index, internal

    return result_parser

def _bracket_wrapped_parser(internal_parser):
    return _wrapped_parser('open_bracket', 'close_bracket', internal_parser)

def _parenthese_wrapped_parser(internal_parser):
    return _wrapped_parser('open_parenthese', 'close_parenthese', internal_parser)

def _parenthesized_expression_parser(index, tokens):
    return _parenthese_wrapped_parser(_expression_parser)(index, tokens)

def symbol_expression_pair_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type == 'symbol':
        symbol = tokens[index].match
        index += 1
    else:
        return failure

    if tokens[index].type == 'colon':
        index += 1
    else:
        return failure

    success, index, expression = _expression_parser(index, tokens)

    if not success:
        raise Exception()

    return (
        True,
        index,
        FurSymbolExpressionPair(
            symbol=symbol,
            expression=expression,
        ),
    )

def _structure_literal_parser(index, tokens):
    success, index, result = _parenthese_wrapped_parser(_comma_separated_list_parser(symbol_expression_pair_parser))(index, tokens)
    return (
        success,
        index,
        FurStructureLiteralExpression(
            fields=result,
        ),
    )

def _list_literal_expression_parser(index, tokens):
    failure = (False, index, None)

    success, index, item_expression_list = _bracket_wrapped_parser(_comma_separated_expression_list_parser)(index, tokens)

    if success:
        return success, index, FurListLiteralExpression(
            item_expression_list=item_expression_list,
        )
    else:
        return failure

def _literal_level_expression_parser(index, tokens):
    return _or_parser(
        _list_item_expression_parser,
        _function_call_expression_parser,
        _parenthesized_expression_parser,
        _integer_literal_expression_parser,
        _string_literal_expression_parser,
        _list_literal_expression_parser,
        _symbol_expression_parser,
        _structure_literal_parser,
    )(index, tokens)

def _dot_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'period',
        _literal_level_expression_parser,
        'dot_level',
    )(index, tokens)

def _negation_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].match != '-':
        return failure

    metadata = NodeMetadata(
        index=tokens[index].index,
        line=tokens[index].line,
    )

    success, index, value = _dot_expression_parser(index + 1, tokens)

    if not success:
        return failure

    return (True, index, FurNegationExpression(metadata=metadata, value=value))

def _negation_level_expression_parser(index, tokens):
    return _or_parser(
        _dot_expression_parser,
        _negation_expression_parser,
    )(index, tokens)

def _left_recursive_infix_operator_parser(operator_token_matcher, operand_parser, order):
    def result_parser(index, tokens):
        failure = (False, index, None)

        success, index, result = operand_parser(index, tokens)

        if not success:
            return failure

        while success and index < len(tokens) and operator_token_matcher(tokens[index]):
            success = False

            if index + 1 < len(tokens):
                success, try_index, value = operand_parser(index + 1, tokens)

            if success:
                result = FurInfixExpression(
                    metadata=NodeMetadata(
                        index=tokens[index].index,
                        line=tokens[index].line,
                    ),
                    order=order,
                    operator=tokens[index].match,
                    left=result,
                    right=value,
                )
                index = try_index

        return True, index, result

    return result_parser

def _multiplication_level_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'multiplication_level_operator',
        _negation_level_expression_parser,
        'multiplication_level',
    )(index, tokens)

def _addition_level_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'addition_level_operator',
        _multiplication_level_expression_parser,
        'addition_level',
    )(index, tokens)

def _comparison_level_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'comparison_level_operator',
        _addition_level_expression_parser,
        'comparison_level',
    )(index, tokens)

def _and_level_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'symbol' and token.match == 'and',
        _comparison_level_expression_parser,
        'and_level',
    )(index, tokens)

def _or_level_expression_parser(index, tokens):
    return _left_recursive_infix_operator_parser(
        lambda token: token.type == 'symbol' and token.match == 'or',
        _and_level_expression_parser,
        'or_level',
    )(index, tokens)

def _comma_separated_list_parser(subparser):
    def result_parser(index, tokens):
        start_index = index

        items = []

        _, index, _ = consume_newlines(index, tokens)

        success, index, item = subparser(index, tokens)

        if success:
            items.append(item)
        else:
            return (True, start_index, ())

        while success and index < len(tokens) and tokens[index].type == 'comma':
            index += 1
            success = False

            _, index, _ = consume_newlines(index, tokens)

            if index < len(tokens):
                success, try_index, item = subparser(index, tokens)

            if success:
                items.append(item)
                index = try_index

        return True, index, tuple(items)

    return result_parser

def _comma_separated_expression_list_parser(index, tokens):
    return _comma_separated_list_parser(_expression_parser)(index, tokens)

FurListItemExpression = collections.namedtuple(
    'FurListItemExpression',
    [
        'list_expression',
        'metadata',
        'index_expression',
    ],
)

FurFunctionCallExpression = collections.namedtuple(
    'FurFunctionCallExpression',
    [
        'function',
        'arguments',
    ],
)

FurExpressionStatement = collections.namedtuple(
    'FurExpressionStatement',
    [
        'expression',
    ],
)

FurAssignmentStatement = collections.namedtuple(
    'FurAssignmentStatement',
    [
        'target',
        'expression',
    ],
)

FurFunctionDefinitionStatement = collections.namedtuple(
    'FurFunctionDefinitionStatement',
    [
        'name',
        'argument_name_list',
        'statement_list',
    ],
)

FurProgram = collections.namedtuple(
    'FurProgram',
    [
        'statement_list',
    ],
)

def _list_item_expression_parser(index, tokens):
    failure = (False, index, None)

    # We have to be careful what expressions we add here. Otherwise expressions
    # like "a + b[0]" become ambiguous to the parser.
    success, index, list_expression = _or_parser(
        _symbol_expression_parser,
        _parenthesized_expression_parser,
    )(index, tokens)

    if not success:
        return failure

    metadata = NodeMetadata(
        index=tokens[index].index,
        line=tokens[index].line,
    )

    success, index, index_expression = _bracket_wrapped_parser(_expression_parser)(
        index,
        tokens,
    )

    if not success:
        return failure

    while success and index < len(tokens):
        # "list_expression" is actually the full list item expression if the next parse attempt doesn't succeed
        # We can't give this a better name without a bunch of checks, however.
        list_expression = FurListItemExpression(
            list_expression=list_expression,
            metadata=metadata,
            index_expression=index_expression,
        )

        metadata = NodeMetadata(
            index=tokens[index].index,
            line=tokens[index].line,
        )

        success, index, index_expression = _bracket_wrapped_parser(_expression_parser)(
            index,
            tokens,
        )

    return True, index, list_expression

def _function_call_expression_parser(index, tokens):
    failure = (False, index, None)

    # We have to be careful what expressions we add here. Otherwise expressions
    # like "a + b()" become ambiguous to the parser.
    success, index, function = _or_parser(
        _symbol_expression_parser,
        _parenthesized_expression_parser,
    )(index, tokens)

    if not success:
        return failure

    success, index, arguments = _parenthese_wrapped_parser(_comma_separated_expression_list_parser)(
        index,
        tokens,
    )

    if not success:
        return failure

    while success and index < len(tokens):
        # "function" is actually the full function call if the next parse attempt doesn't succeed
        # We can't give this a better name without a bunch of checks, however.
        function = FurFunctionCallExpression(
            function=function,
            arguments=arguments,
        )

        success, index, arguments = _parenthese_wrapped_parser(_comma_separated_expression_list_parser)(
            index,
            tokens,
        )

    return True, index, function

def _if_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].match == 'if':
        index += 1
    else:
        return failure

    success, index, condition_expression = _or_level_expression_parser(index, tokens)

    if not success:
        raise Exception('Expected condition after "if" on line {}'.format(tokens[index].line))

    if tokens[index].match == 'do':
        index += 1
    else:
        raise Exception('Expected "do" after "if" on line {}'.format(tokens[index].line))


    success, index, if_statement_list = _zero_or_more_parser(tuple, _statement_parser)(index, tokens)
    _, index, _ = consume_newlines(index, tokens)

    if tokens[index].match == 'else':
        index += 1
        success, index, else_statement_list = _zero_or_more_parser(tuple, _statement_parser)(index, tokens)
        _, index, _ = consume_newlines(index, tokens)
    else:
        else_statement_list = ()

    if tokens[index].match == 'end':
        index += 1
    else:
        raise Exception('Expected "end" after "if" on line {}'.format(tokens[index].line))

    return (
        True,
        index,
        FurIfExpression(
            condition_expression=condition_expression,
            if_statement_list=if_statement_list,
            else_statement_list=else_statement_list,
        ),
    )

_expression_parser = _or_parser(
    _or_level_expression_parser,
    _if_expression_parser, # This should always be at the top level
)

def _expression_statement_parser(index, tokens):
    failure = (False, index, None)

    success, index, expression = _expression_parser(index, tokens)

    if not success:
        return failure

    return (True, index, FurExpressionStatement(expression=expression))

BUILTINS = {'print', 'pow'}

def _assignment_statement_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type == 'symbol':
        target = tokens[index].match
        target_assignment_line = tokens[index].line

        index += 1
    else:
        return failure


    if tokens[index].type == 'assignment_operator':
        if target in BUILTINS:
            raise Exception(
                'Trying to assign to builtin "{}" on line {}'.format(target, target_assignment_line),
            )
        assignment_operator_index = index
    else:
        return failure

    success, index, expression = _expression_parser(index + 1, tokens)

    if not success:
        raise Exception(
            'Expected expression after assignment operator on line {}'.format(
                tokens[assignment_operator_index].line
            )
        )

    return True, index, FurAssignmentStatement(target=target, expression=expression)

def _function_definition_statement_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type == 'keyword' and tokens[index].match == 'def':
        index += 1
    else:
        return failure

    if tokens[index].type == 'symbol':
        name = tokens[index].match
        index += 1
    else:
        raise Exception('Expected function name, found "{}" on line {}'.format(
            tokens[index].match,
            tokens[index].line,
        ))

    if tokens[index].type == 'open_parenthese':
        index += 1
    else:
        raise Exception('Expected "(", found "{}" on line {}'.format(
            tokens[index].match,
            tokens[index].line,
        ))

    success, index, argument_name_list = _comma_separated_list_parser(_symbol_expression_parser)(
        index,
        tokens,
    )

    if tokens[index].type == 'close_parenthese':
        index += 1
    else:
        raise Exception('Expected ")", found "{}" on line {}'.format(
            tokens[index].match,
            tokens[index].line,
        ))

    if tokens[index].match == 'do':
        index += 1
    else:
        return failure

    success, index, statement_list = _zero_or_more_parser(tuple, _statement_parser)(index, tokens)

    _, index, _ = consume_newlines(index, tokens)

    if tokens[index].type == 'keyword' and tokens[index].match == 'end':
        index += 1
    else:
        return failure

    return True, index, FurFunctionDefinitionStatement(
        name=name,
    argument_name_list=tuple(an.symbol for an in argument_name_list),
        statement_list=statement_list,
    )

def _statement_parser(index, tokens):
    _, index, _ = consume_newlines(index, tokens)

    if index == len(tokens):
        return (False, index, None)

    return _or_parser(
        _assignment_statement_parser,
        _expression_statement_parser,
        _function_definition_statement_parser,
    )(index, tokens)

def _program_formatter(statement_list):
    return FurProgram(statement_list=statement_list)

_program_parser = _zero_or_more_parser(_program_formatter, _statement_parser)

def _parse(parser, tokens):
    success, index, result = parser(0, tokens)

    if index < len(tokens):
        raise Exception('Unable to parse token {}'.format(tokens[index]))

    if success:
        return result

    raise Exception('Unable to parse')

def parse(tokens):
    return _parse(_program_parser, tokens)

if __name__ == '__main__':
    import unittest

    import tokenization

    class FurStringLiteralExpressionParserTests(unittest.TestCase):
        def test_parses_single_quoted_string_literal(self):
            self.assertEqual(
                _string_literal_expression_parser(0, tokenization.tokenize("'Hello, world'")),
                (
                    True,
                    1,
                    FurStringLiteralExpression(string='Hello, world'),
                ),
            )

    class FurFunctionCallExpressionParserTests(unittest.TestCase):
        def test_parses_function_with_string_literal_argument(self):
            self.assertEqual(
                _function_call_expression_parser(0, tokenization.tokenize("print('Hello, world')")),
                (
                    True,
                    4,
                    FurFunctionCallExpression(
                        name='print',
                        arguments=(FurStringLiteralExpression(string='Hello, world'),),
                    ),
                ),
            )

    unittest.main()
