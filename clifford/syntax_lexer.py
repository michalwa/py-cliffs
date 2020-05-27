from typing import Iterable, Tuple
from .utils import StrBuffer


class SyntaxLexer:
    def tokenize(self, spec: str) -> Iterable[Tuple[str, str]]:
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
