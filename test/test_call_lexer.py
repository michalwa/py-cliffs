from unittest import TestCase
from cliffs.call_lexer import CallLexer


class TestCallLexer(TestCase):

    def setUp(self):
        self.lexer = CallLexer()

    def assertLexerYields(self, string, expected):
        result = self.lexer.tokenize(string)
        actual = list((token.value, token.start, token.end) for token in result)
        self.assertListEqual(expected, actual)

    def test_empty(self):
        self.assertLexerYields('', [])

    def test_singlePlain(self):
        self.assertLexerYields('foo', [('foo', 0, 3)])
        self.assertLexerYields('  foo  ', [('foo', 2, 5)])

    def test_multiplePlain(self):
        self.assertLexerYields(
            'foo bar baz', [
                ('foo', 0, 3),
                ('bar', 4, 7),
                ('baz', 8, 11)
            ])

        self.assertLexerYields(
            '  foo  bar  baz  ', [
                ('foo', 2, 5),
                ('bar', 7, 10),
                ('baz', 12, 15)
            ])

    def test_singleQuoted(self):
        self.assertLexerYields('"foo"', [('foo', 0, 5)])
        self.assertLexerYields('"  foo  "', [('  foo  ', 0, 9)])
        self.assertLexerYields('  "  foo  "  ', [('  foo  ', 2, 11)])

    def test_multipleQuoted(self):
        self.assertLexerYields(
            '"foo" "bar""baz"', [
                ('foo', 0, 5),
                ('bar', 6, 11),
                ('baz', 11, 16)
            ])

        self.assertLexerYields(
            '"  foo" " bar ""baz  "', [
                ('  foo', 0, 7),
                (' bar ', 8, 15),
                ('baz  ', 15, 22)
            ])

    def test_plainEscape(self):
        """Escaped quotes outside of quoted strings should keep the backslash"""

        self.assertLexerYields('\\"', [('\\"', 0, 2)])
        self.assertLexerYields('  \\"  ', [('\\"', 2, 4)])

    def test_singleQuotedWithEscape(self):
        self.assertLexerYields('"\\""', [('"', 0, 4)])
        self.assertLexerYields('"foo \\"bar\\""', [('foo "bar"', 0, 13)])

    def test_unterminatedQuote(self):
        """Unterminated quoted tokens should be treated as plain tokens together
        with the initial quote character."""

        self.assertLexerYields('"', [('"', 0, 1)])
        self.assertLexerYields('foo "', [('foo', 0, 3), ('"', 4, 5)])
        self.assertLexerYields('"foo', [('"foo', 0, 4)])
        self.assertLexerYields('foo "bar', [('foo', 0, 3), ('"bar', 4, 8)])

    def test_unterminatedEscape(self):
        """Unterminated escape sequences should keep the backslash"""

        self.assertLexerYields('\\', [('\\', 0, 1)])
        self.assertLexerYields('foo\\', [('foo\\', 0, 4)])
        self.assertLexerYields(
            'foo \\', [
                ('foo', 0, 3),
                ('\\', 4, 5)
            ])

    def test_unsupportedEscape(self):
        """Unsupported escape characters should be left as they are keeping the backslash."""

        self.assertLexerYields('\\a', [('\\a', 0, 2)])
