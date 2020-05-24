from typing import Iterator, Tuple
from .utils import StrBuffer


class SyntaxLexer:
    def tokenize(self, spec: str) -> Iterator[Tuple[str, str]]:
        current = StrBuffer()  # the current token being accumulated
        end = False            # whether a delimiter occured while parsing the current token
        parsing_param = False  # whether parsing a parameter

        for c in spec:

            # Treat spaces as delimiters but exclude from tokens
            if c.isspace():
                end = True

            # Delimiters
            elif c in '[](|)':
                if parsing_param:
                    raise SyntaxError('Unterminated parameter expression')
                if current != '':
                    yield 'literal', current.flush()
                yield 'delim', c

            # Parameters
            elif c == '<':
                if parsing_param:
                    raise SyntaxError("Unexpected parameter opening delimiter '<'")
                parsing_param = True
            elif c == '>':
                if not parsing_param:
                    raise SyntaxError("Unexpected parameter closing delimiter '>'")
                if current == '':
                    raise SyntaxError('Empty parameter name')

                yield 'param', current.flush()
                parsing_param = False

            # Literals & param names
            else:
                if end:
                    if current != '':
                        yield 'literal', current.flush()
                    end = False
                current += c

        if parsing_param:
            raise SyntaxError('Unterminated parameter expression')

        if current != '':
            yield 'literal', current.flush()
