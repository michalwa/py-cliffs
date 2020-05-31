from typing import Optional


class StrBuffer:
    def __init__(self):
        self._buffer = ''

    def flush(self) -> str:
        temp, self._buffer = self._buffer, ''
        return temp

    def trim(self, start: Optional[int] = None, end: Optional[int] = None):
        if start is None:
            if end is not None:
                self._buffer = self._buffer[:end]
        else:
            if end is None:
                self._buffer = self._buffer[start:]
            else:
                self._buffer = self._buffer[start:end]

    def __iadd__(self, seq: str) -> 'StrBuffer':
        self._buffer += seq
        return self

    def __str__(self) -> str:
        return self._buffer

    def __eq__(self, other) -> bool:
        return any([
            self is other,
            self._buffer == other,
            isinstance(other, self.__class__) and self._buffer == other._buffer
        ])


def loose_bool(s: str) -> bool:
    try:
        f = float(s)
        return bool(f)
    except:
        pass

    s = s.lower()
    if s in ['y', 'yes', 't', 'true', 'do', 'ok', 'sure', 'alright']:
        return True
    elif s in ['n', 'no', 'f', 'false', 'dont']:
        return False
        
    else:
        raise ValueError(f"String '{s}' cannot be loosely casted to a boolean")
