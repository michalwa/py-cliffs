from typing import Generator, Tuple
from .utils import StrBuffer


class SyntaxLexer:
    def tokenize(self, spec: str) -> Generator[Tuple[str, str], None, None]:
        current = StrBuffer()

        for c in spec + ' ':

            # Treat spaces as delimiters but exclude from tokens
            if c.isspace():
                if current != '':
                    yield 'literal', current.flush()

            # Delimiters
            elif c in '<:>[](|)':
                if current != '':
                    yield 'literal', current.flush()
                yield 'delim', c

            # Accumulate literals
            else:
                current += c

        if current != '':
            yield 'literal', current.flush()
