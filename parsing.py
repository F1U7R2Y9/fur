import collections

StringLiteral = collections.namedtuple(
    'StringLiteral',
    [
        'value',
    ],
)

def _string_literal_parser(index, tokens):
    failure = (False, index, None)

    if tokens[index].type != 'single_quoted_string_literal':
        return failure
    value = tokens[index].match[1:-1]
    index += 1

    return True, index, StringLiteral(value=value)


FunctionCall = collections.namedtuple(
    'FunctionCall',
    [
        'name',
        'arguments',
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

    success, index, argument = _string_literal_parser(index, tokens)

    if not success:
        return failure

    if tokens[index].type != 'close_parenthese':
        return failure
    index += 1
    
    return True, index, FunctionCall(name=name, arguments=(argument,))

def _parse(parser, tokens):
    success, index, result = parser(0, tokens)

    if success:
        return result

    raise Exception('Unable to parse')


def parse(tokens):
    return _parse(_function_call_parser, tokens)

if __name__ == '__main__':
    import unittest

    import tokenization

    class StringLiteralParserTests(unittest.TestCase):
        def test_parses_single_quoted_string_literal(self):
            self.assertEqual(
                _string_literal_parser(0, tokenization.tokenize("'Hello, world'")),
                (
                    True,
                    1,
                    StringLiteral(value='Hello, world'),
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
                        arguments=(StringLiteral(value='Hello, world'),),
                    ),
                ),
            )

    unittest.main()
