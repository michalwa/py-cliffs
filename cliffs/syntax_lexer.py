from typing import Iterable
from .utils import StrBuffer
from .token import Token


class SyntaxLexer:
    """Splits syntax specification strings into tokens."""

    def tokenize(self, spec: str) -> Iterable[Token]:
        """Splits the specified syntax specification into tokens.

        Parameters
        ----------
          * spec: `str` - The specification string to tokenize.

        Returns
        -------
          * `Iterable[Token]`: The resulting tokens.
        """

        current_start = 0
        current = StrBuffer()

        for i, c in enumerate(spec + ' '):

            # Treat spaces as delimiters but exclude from tokens
            if c.isspace():
                if current != '':
                    yield Token('symbol', current.flush(), current_start, i)

            # Accumulate symbols
            else:
                if current == '':
                    current_start = i

                current += c

                # Trim off accumulated punctuation tokens
                for punct in list('<>()[]{}:|*^~') + ['...']:
                    if str(current).endswith(punct):
                        current.trim(end=-len(punct))
                        if current != '':
                            yield Token('symbol', current.flush(), current_start, i - len(punct) + 1)

                        yield Token(None, punct, i - len(punct) + 1, i + 1)
