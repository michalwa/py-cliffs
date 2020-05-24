from typing import Iterator, Optional
from .utils import StrBuffer


class CallLexer:
    def __init__(self, delims='"\''):
        self.delims = delims

    def tokenize(self, cmd: str) -> Iterator[str]:
        current = StrBuffer()
        delim = None  # type: Optional[str]

        for c in cmd + ' ':
            if c.isspace():
                if current != '':
                    if delim:
                        current += c
                    else:
                        yield current.flush()
            
            elif c in self.delims:
                if delim is None:
                    delim = c
                elif c == delim:
                    yield current.flush()
                    delim = None
                else:
                    current += c

            else:
                current += c
