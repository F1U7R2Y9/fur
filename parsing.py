import collections

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

FurIntegerLiteralExpression = collections.namedtuple(
    'FurIntegerLiteralExpression',
    [
        'value',
    ],
)

FurStringLiteralExpression = collections.namedtuple(
    'FurStringLiteralExpression',
    [
        'value',
    ],
)

FurSymbolExpression = collections.namedtuple(
    'FurSymbolExpression',
    [
        'value',
    ],
)

FurNegationExpression = collections.namedtuple(
    'FurNegationExpression',
    [
        'value',
    ],
)

FurParenthesizedExpression = collections.namedtuple(
    'FurParenthesizedExpression',
    [
        'internal',
    ],
)

FurAdditionExpression = collections.namedtuple(
    'FurAdditionExpression',
    [
        'left',
        'right',
    ],
)

FurSubtractionExpression = collections.namedtuple(
    'FurSubtractionExpression',
    [
        'left',
        'right',
    ],
)

FurMultiplicationExpression = collections.namedtuple(
    'FurMultiplicationExpression',
    [
        'left',
        'right',
    ],
)

FurIntegerDivisionExpression = collections.namedtuple(
    'FurIntegerDivisionExpression',
    [
        'left',
        'right',
    ],
)

FurModularDivisionExpression = collections.namedtuple(
    'FurModularDivisionExpression',
    [
        'left',
        'right',
    ],
)

def _integer_literal_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type != 'integer_literal':
        return failure
    value = int(tokens[index].match)
    index += 1

    return True, index, FurIntegerLiteralExpression(value=value)

def _string_literal_expression_parser(index, tokens):
    if tokens[index].type == 'single_quoted_string_literal':
        return (True, index + 1, FurStringLiteralExpression(value=tokens[index].match[1:-1]))

    return (False, index, None)

def _symbol_expression_parser(index, tokens):
    if tokens[index].type == 'symbol':
        return (True, index + 1, FurSymbolExpression(value=tokens[index].match))

    return (False, index, None)

def _parenthesized_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type == 'open_parenthese':
        index += 1
    else:
        return failure

    success, index, internal = _expression_parser(index, tokens)
    if not success:
        return failure

    if tokens[index].type == 'close_parenthese':
        index += 1
    else:
        raise Exception('Expected ")" on line {}, found "{}"'.format(
            tokens[index].line,
            tokens[index].match,
        ))

    return True, index, FurParenthesizedExpression(internal=internal)

def _negation_expression_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].match != '-':
        return failure

    success, index, value = _literal_level_expression_parser(index + 1, tokens)

    if not success:
        return failure

    return (True, index, FurNegationExpression(value=value))

def _literal_level_expression_parser(index, tokens):
    return _or_parser(
        _negation_expression_parser,
        _function_call_expression_parser,
        _parenthesized_expression_parser,
        _integer_literal_expression_parser,
        _string_literal_expression_parser,
        _symbol_expression_parser,
    )(index, tokens)

def _multiplication_level_expression_parser(index, tokens):
    failure = (False, index, None)

    success, index, result = _literal_level_expression_parser(index, tokens)

    if not success:
        return failure

    while success and index < len(tokens) and tokens[index].type == 'multiplication_level_operator':
        success = False

        if index + 1 < len(tokens):
            success, try_index, value = _literal_level_expression_parser(index + 1, tokens)

        if success:
            result = {
                '*': FurMultiplicationExpression,
                '//': FurIntegerDivisionExpression,
                '%': FurModularDivisionExpression,
            }[tokens[index].match](left=result, right=value)
            index = try_index

    return True, index, result

def _addition_level_expression_parser(index, tokens):
    failure = (False, index, None)

    success, index, result = _multiplication_level_expression_parser(index, tokens)

    if not success:
        return failure

    while success and index < len(tokens) and tokens[index].type == 'addition_level_operator':
        success = False

        if index + 1 < len(tokens):
            success, try_index, value = _multiplication_level_expression_parser(index + 1, tokens)

        if success:
            result = {
                '+': FurAdditionExpression,
                '-': FurSubtractionExpression,
            }[tokens[index].match](left=result, right=value)
            index = try_index

    return True, index, result

def _comma_separated_list_parser(index, tokens):
    failure = (False, index, None)

    expressions = []

    success, index, expression = _addition_level_expression_parser(index, tokens)

    if success:
        expressions.append(expression)
    else:
        return failure

    while success and index < len(tokens) and tokens[index].type == 'comma':
        success = False

        if index + 1 < len(tokens):
            success, try_index, expression = _addition_level_expression_parser(index + 1, tokens)

        if success:
            expressions.append(expression)
            index = try_index

    return True, index, tuple(expressions)


FurFunctionCallExpression = collections.namedtuple(
    'FurFunctionCallExpression',
    [
        'function',
        'arguments',
    ],
)

FurAssignmentStatement = collections.namedtuple(
    'FurAssignmentStatement',
    [
        'target',
        'expression',
    ],
)

FurProgram = collections.namedtuple(
    'FurProgram',
    [
        'statement_list',
    ],
)

def _function_call_expression_parser(index, tokens):
    # TODO Use a FurSymbolExpression for the name
    failure = (False, index, None)

    success, index, function = _symbol_expression_parser(index, tokens)

    if not success:
        return failure

    if tokens[index].type != 'open_parenthese':
        return failure
    index += 1

    success, index, arguments = _comma_separated_list_parser(index, tokens)

    if not success:
        return failure

    if tokens[index].type != 'close_parenthese':
        raise Exception('Expected ")", found "{}" on line {}'.format(
            tokens[index].match,
            tokens[index].line,
        ))
    index += 1

    return True, index, FurFunctionCallExpression(function=function, arguments=arguments)

_expression_parser = _addition_level_expression_parser

def _assignment_statement_parser(index, tokens):
    # TODO Use a FurSymbolExpression for the target
    failure = (False, index, None)

    if tokens[index].type != 'symbol':
        return failure
    target = tokens[index].match
    index += 1

    if tokens[index].type != 'assignment_operator':
        return failure
    assignment_operator_index = index

    success, index, expression = _expression_parser(index + 1, tokens)

    if not success:
        raise Exception(
            'Expected expression after assignment operator on line {}'.format(
                tokens[assignment_operator_index].line
            )
        )

    return True, index, FurAssignmentStatement(target=target, expression=expression)

def _statement_parser(index, tokens):
    return _or_parser(
        _assignment_statement_parser,
        _expression_parser,
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
                    FurStringLiteralExpression(value='Hello, world'),
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
                        arguments=(FurStringLiteralExpression(value='Hello, world'),),
                    ),
                ),
            )

    unittest.main()
