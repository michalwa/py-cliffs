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

            # Delimiters
            elif c in '<:>|()[]{}':
                if current != '':
                    yield Token('symbol', current.flush(), current_start, i)
                yield Token('delimeter', c, i, i + 1)

            # Asterisk
            elif c == '*':
                if current != '':
                    yield Token('symbol', current.flush(), current_start, i)
                yield Token('asterisk', c, i, i + 1)

            # Accumulate symbols
            else:
                if current == '':
                    current_start = i

                current += c

                # Yield off ellipses
                if str(current).endswith('...'):
                    current.trim(end=-3)
                    if current != '':
                        yield Token('symbol', current.flush(), current_start, i - 2)
                    yield Token('ellipsis', '...', i - 2, i + 1)
