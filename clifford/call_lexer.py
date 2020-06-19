from typing import Iterable, Optional
from .utils import StrBuffer


class CallLexer:
    def __init__(self, delims: str = '"\''):
        self.delims = delims

    def tokenize(self, cmd: str) -> Iterable[str]:
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
                current += c
