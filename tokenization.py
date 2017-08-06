import collections
import re

import util

Token = collections.namedtuple(
    'Token',
    [
        'type',
        'match',
        'index',
        'line',
    ],
)

def _make_token_matcher(definition):
    name, regex = definition
    regex_matcher = re.compile(regex)

    def token_matcher(index, source, line):
        match = regex_matcher.match(source[index:])

        if match is None:
            return False, index, None

        return (
            True,
            index + len(match.group()),
            Token(type=name, match=match.group(), index=index, line=line),
        )

    return token_matcher


_TOKEN_MATCHERS = [
    ('open_parenthese',                 r'\('),
    ('close_parenthese',                r'\)'),
    ('comma',                           r','),
    ('integer_literal',                 r'\d+'),
    ('symbol',                          r'[a-z]+'),
    ('single_quoted_string_literal',    r"'.*?'"),
    ('equality_level_operator',         r'(<=|>=|==|!=|<|>)'),
    ('assignment_operator',             r'='),
    ('addition_level_operator',         r'(\+|-)'),
    ('multiplication_level_operator',   r'(\*|//|%)'),
]

_TOKEN_MATCHERS = list(map(_make_token_matcher, _TOKEN_MATCHERS))

@util.force_generator(tuple)
def tokenize(source):
    index = 0
    line = 1

    while index < len(source):
        if source[index] == ' ':
            index += 1
            continue

        success = False

        for matcher in _TOKEN_MATCHERS:
            success, index, token = matcher(index, source, line)

            if success:
                yield token
                break

        if not success:
            raise Exception('Unexpected character "{}"'.format(source[index]))

        while index < len(source) and source[index] in set(['\n']):
            line += 1
            index += 1

if __name__ == '__main__':
    import unittest

    class TokenizeTests(unittest.TestCase):
        def test_tokenizes_open_parenthese(self):
            self.assertEqual(
                tokenize('('),
                (Token(
                    type='open_parenthese',
                    match='(',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_close_parenthese(self):
            self.assertEqual(
                tokenize(')'),
                (Token(
                    type='close_parenthese',
                    match=')',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_symbol(self):
            self.assertEqual(
                tokenize('print'),
                (Token(
                    type='symbol',
                    match='print',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_single_quoted_string_literal(self):
            self.assertEqual(
                tokenize("'Hello, world'"),
                (Token(
                    type='single_quoted_string_literal',
                    match="'Hello, world'",
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_plus(self):
            self.assertEqual(
                tokenize('+'),
                (Token(
                    type='addition_level_operator',
                    match='+',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_minus(self):
            self.assertEqual(
                tokenize('-'),
                (Token(
                    type='addition_level_operator',
                    match='-',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_times(self):
            self.assertEqual(
                tokenize('*'),
                (Token(
                    type='multiplication_level_operator',
                    match='*',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_integer_divide(self):
            self.assertEqual(
                tokenize('//'),
                (Token(
                    type='multiplication_level_operator',
                    match='//',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_modular_divide(self):
            self.assertEqual(
                tokenize('%'),
                (Token(
                    type='multiplication_level_operator',
                    match='%',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_comma(self):
            self.assertEqual(
                tokenize(','),
                (Token(
                    type='comma',
                    match=',',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_assignment_operator(self):
            self.assertEqual(
                tokenize('='),
                (Token(
                    type='assignment_operator',
                    match='=',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_equality_operator(self):
            self.assertEqual(
                tokenize('=='),
                (Token(
                    type='equality_level_operator',
                    match='==',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_greater_than_or_equal_operator(self):
            self.assertEqual(
                tokenize('>='),
                (Token(
                    type='equality_level_operator',
                    match='>=',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_less_than_or_equal_operator(self):
            self.assertEqual(
                tokenize('<='),
                (Token(
                    type='equality_level_operator',
                    match='<=',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_greater_than_equal_operator(self):
            self.assertEqual(
                tokenize('>'),
                (Token(
                    type='equality_level_operator',
                    match='>',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_less_than_equal_operator(self):
            self.assertEqual(
                tokenize('<'),
                (Token(
                    type='equality_level_operator',
                    match='<',
                    index=0,
                    line=1,
                ),),
            )

        def test_tokenizes_not_equal_operator(self):
            self.assertEqual(
                tokenize('!='),
                (Token(
                    type='equality_level_operator',
                    match='!=',
                    index=0,
                    line=1,
                ),),
            )

        def test_handles_trailing_newline(self):
            self.assertEqual(
                tokenize('print\n'),
                (Token(
                    type='symbol',
                    match='print',
                    index=0,
                    line=1,
                ),),
            )

        def test_handles_leading_space(self):
            self.assertEqual(
                tokenize(' print'),
                (Token(
                    type='symbol',
                    match='print',
                    index=1,
                    line=1,
                ),),
            )

        def test_tokenizes_with_proper_line_numbers(self):
            self.assertEqual(
                tokenize('print\n('),
                (
                    Token(
                        type='symbol',
                        match='print',
                        index=0,
                        line=1,
                    ),
                    Token(
                        type='open_parenthese',
                        match='(',
                        index=6,
                        line=2,
                    ),
                ),
            )


    unittest.main()
