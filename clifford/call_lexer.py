from typing import Iterable, Optional
from .utils import StrBuffer


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

    def tokenize(self, cmd: str) -> Iterable[str]:
        """Splits the given command call string into string tokens.

        Parameters
        ----------
          * cmd: `str` - The call to tokenize.

        Returns
        -------
          * `Iterable[str]`: The resulting tokens.
        """

        current = StrBuffer()
        escape = False
        delim = None  # type: Optional[str]

        for c in cmd + ' ':
            if c.isspace():
                if current != '':
                    if delim:
                        current += c
                    else:
                        yield current.flush()

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
                elif c == delim:
                    yield current.flush()
                    delim = None
                else:
                    current += c

            else:
                if escape:
                    current += '\\'
                    escape = False
                current += c
