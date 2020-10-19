from typing import Iterable
from .token import Token


class CallLexer:
    """Splits command calls into tokens.
    This is the first module a command call passes through upon being issued.

    By default a lexer is configured to use ' and " as delimiters (similar to
    how they work in Python, with support for escapement).
    """

    def __init__(self, quotes: str = '"\''):
        """Initializes a call lexer.

        Parameters
        ----------
          * quotes: `str` - The characters to use as compound quoted token delimiters
            (used to include spaces in tokens). Defaults to `'` and `"`.
        """

        self.quotes = quotes

    def tokenize(self, cmd: str) -> Iterable[Token]:
        """Splits the given command call string into tokens.

        Parameters
        ----------
          * cmd: `str` - The call to tokenize.

        Returns
        -------
          * `Iterable[Token]`: The resulting tokens.
        """

        current = ''
        current_start = 0
        quote = None
        escape = False

        def plain_token(end: int):
            return Token(None, current, current_start, end)

        def quoted_token(end: int):
            if quote is None:
                raise RuntimeError("Something went horribly wrong")
            return Token(None, quote + current + quote, current_start, end, value=current)

        i = 0
        for i, c in enumerate(cmd):

            if c.isspace() and quote is None:
                if current != '':
                    yield plain_token(i)
                current = ''
                current_start = i + 1

            elif c in self.quotes:

                # Escaped quote
                if escape:
                    # Keep escape character if not inside a quoted token
                    if quote is None:
                        current += '\\'
                    current += c
                    escape = False

                # Begin quoted token
                elif quote is None:
                    if current != '':
                        yield plain_token(i)
                    current = ''
                    current_start = i
                    quote = c

                # End quoted token
                elif quote == c:
                    yield quoted_token(i + 1)
                    current = ''
                    quote = None

            elif c == '\\':

                # Escaped backslash
                if escape:
                    current += c
                    escape = False

                # Begin escape
                else:
                    escape = True

            else:
                # Backslash doesn't do anything if escaping an non-escapable character
                if escape:
                    current += '\\'
                    escape = False

                current += c

        # Unterminated escape sequence
        if escape:
            current += '\\'

        # Unterminated quoted token
        if quote is not None:
            yield Token(None, quote + current, current_start, i + 1, value=quote + current)

        # Leftover plain token
        elif current != '':
            yield plain_token(i + 1)
