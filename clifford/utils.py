class StrBuffer:
    def __init__(self):
        self._buffer = ''

    def flush(self) -> str:
        temp, self._buffer = self._buffer, ''
        return temp

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
        if f == 1:
            return True
        elif f == 0:
            return False
    except:
        pass

    s = s.lower()
    if s in ['y', 'yes', 't', 'true', 'do', 'ok', 'sure', 'alright']:
        return True
    elif s in ['n', 'no', 'f', 'false', 'dont']:
        return False
        
    else:
        raise ValueError(f"String '{s}' cannot be loosely casted to a boolean")
