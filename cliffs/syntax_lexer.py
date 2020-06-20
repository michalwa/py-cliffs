from typing import Iterable, Tuple
from .utils import StrBuffer


class SyntaxLexer:
    """Splits syntax specification strings into tokens."""

    def tokenize(self, spec: str) -> Iterable[Tuple[str, str]]:
        """Splits the specified syntax specification into tokens.

        Parameters
        ----------
          * spec: `str` - The specification string to tokenize.

        Returns
        -------
          * `Iterable[(str, str)]`: The resulting tokens. Each token is a pair of
            two strings: the type of the token (`symbol`, `delim` or `ellipsis`)
            and the value of the token (varies depending on the type).
        """

        current = StrBuffer()

        for c in spec + ' ':

            # Treat spaces as delimiters but exclude from tokens
            if c.isspace():
                if current != '':
                    yield 'symbol', current.flush()

            # Delimiters
            elif c in '<:>[](|)':
                if current != '':
                    yield 'symbol', current.flush()
                yield 'delim', c

            # Accumulate symbols
            else:
                current += c

                # Yield off ellipses
                if str(current).endswith('...'):
                    current.trim(end=-3)
                    if current != '':
                        yield 'symbol', current.flush()
                    yield 'ellipsis', '...'
