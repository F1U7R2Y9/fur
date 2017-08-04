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
    failure = (False, index, None)

    if tokens[index].type != 'single_quoted_string_literal':
        return failure
    value = tokens[index].match[1:-1]
    index += 1

    return True, index, FurStringLiteralExpression(value=value)

def _literal_level_expression_parser(index, tokens):
    return _or_parser(
        _integer_literal_expression_parser,
        _string_literal_expression_parser,
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

FunctionCall = collections.namedtuple(
    'FunctionCall',
    [
        'name',
        'arguments',
    ],
)

FurProgram = collections.namedtuple(
    'FurProgram',
    [
        'statement_list',
    ],
)

def _function_call_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type != 'symbol':
        return failure
    name = tokens[index].match
    index += 1

    if tokens[index].type != 'open_parenthese':
        return failure
    index += 1

    success, index, argument = _addition_level_expression_parser(index, tokens)

    if not success:
        return failure

    if tokens[index].type != 'close_parenthese':
        return failure
    index += 1

    return True, index, FunctionCall(name=name, arguments=(argument,))

def _program_formatter(statement_list):
    return FurProgram(statement_list=statement_list)

_program_parser = _zero_or_more_parser(_program_formatter, _function_call_parser)

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

    class FunctionCallParserTests(unittest.TestCase):
        def test_parses_function_with_string_literal_argument(self):
            self.assertEqual(
                _function_call_parser(0, tokenization.tokenize("print('Hello, world')")),
                (
                    True,
                    4,
                    FunctionCall(
                        name='print',
                        arguments=(FurStringLiteralExpression(value='Hello, world'),),
                    ),
                ),
            )

    unittest.main()
