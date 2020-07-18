from typing import Iterable, Optional
from .utils import StrBuffer
from .token import Token


class CallLexer:
    """Splits command calls into tokens.
    This is the first module a command call passes through upon being issued.

    By default a lexer is configured to use ' and " as delimiters (similar to
    how they work in Python, with support for escapement).
    """

    def __init__(self, delims: str = '"\''):
        """Initializes a call lexer.

        Parameters
        ----------
          * delims: `str` - The characters to use as compound token delimiters
            (used to include spaces in tokens). Defaults to `'` and `"`.
        """

        self.delims = delims

    def tokenize(self, cmd: str) -> Iterable[Token]:
        """Splits the given command call string into tokens.

        Parameters
        ----------
          * cmd: `str` - The call to tokenize.

        Returns
        -------
          * `Iterable[Token]`: The resulting tokens.
        """

        current = StrBuffer()
        current_start = 0
        escape = False
        delim = None  # type: Optional[str]

        for i, c in enumerate(cmd):
            if c.isspace():
                if current != '':
                    if delim:
                        current += c
                    else:
                        yield Token(None, current.flush(), current_start, i)

            elif c == '\\':
                if escape:
                    current += c
                escape = not escape

            elif c in self.delims:
                if escape:
                    current += c
                    escape = False

                elif delim is None:
                    delim = c
                    current_start = i
                elif c == delim:
                    yield Token(None, current.flush(), current_start, i + 1)
                    delim = None
                else:
                    current += c

            else:
                if escape:
                    current += '\\'
                    escape = False

                if current == '':
                    if delim is not None:
                        current_start = i - 1
                    else:
                        current_start = i

                current += c

        if current != '':

            # Unterminated quoted argument
            if delim is not None:
                yield Token(None, delim + current.flush(), current_start, i + 1)

            # Unterminated plain argument
            else:
                yield Token(None, current.flush(), current_start, i + 1)
