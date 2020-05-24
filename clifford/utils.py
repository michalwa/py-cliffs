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
