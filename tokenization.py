import collections
import re

import util

Token = collections.namedtuple(
    'Token',
    [
        'type',
        'match',
    ],
)

def _make_token_matcher(definition):
    name, regex = definition
    regex_matcher = re.compile(regex)

    def token_matcher(index, source):
        match = regex_matcher.match(source[index:])

        if match is None:
            return False, index, None

        return True, index + len(match.group()), Token(type=name, match=match.group())

    return token_matcher


_TOKEN_MATCHERS = [
    ('open_parenthese',                 r'\('),
    ('close_parenthese',                r'\)'),
    ('integer_literal',                 r'-?\s*\d+'),
    ('symbol',                          r'[a-z]+'),
    ('single_quoted_string_literal',    r"'.*?'"),
]

_TOKEN_MATCHERS = list(map(_make_token_matcher, _TOKEN_MATCHERS))

@util.force_generator(tuple)
def tokenize(source):
    index = 0

    while index < len(source):
        success = False

        for matcher in _TOKEN_MATCHERS:
            success, index, token = matcher(index, source)

            if success:
                yield token
                break

        if not success:
            raise Exception('Unexpected character "{}"'.format(source[index]))

        while index < len(source) and source[index] in set(['\n']):
            index += 1

if __name__ == '__main__':
    import unittest

    class TokenizeTests(unittest.TestCase):
        def test_tokenizes_open_parenthese(self):
            self.assertEqual(
                tokenize('('),
                [Token(
                    type='open_parenthese',
                    match='(',
                )],
            )

        def test_tokenizes_close_parenthese(self):
            self.assertEqual(
                tokenize(')'),
                [Token(
                    type='close_parenthese',
                    match=')',
                )],
            )

        def test_tokenizes_symbol(self):
            self.assertEqual(
                tokenize('print'),
                [Token(
                    type='symbol',
                    match='print',
                )],
            )

        def test_tokenizes_single_quoted_string_literal(self):
            self.assertEqual(
                tokenize("'Hello, world'"),
                [Token(
                    type='single_quoted_string_literal',
                    match="'Hello, world'",
                )],
            )

        def test_handles_trailing_newline(self):
            self.assertEqual(
                tokenize('print\n'),
                [Token(
                    type='symbol',
                    match='print',
                )],
            )

    unittest.main()
