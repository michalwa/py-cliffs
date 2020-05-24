from typing import Optional


class CallMatchFail(Exception):
    '''Raised by syntax tree nodes when matching fails in an expected way'''


class CallMatchError(Exception):
    '''Raised by syntax tree nodes when matching fails unexpectedly (because of a mistake in the call)'''


class CallMatch:
    def __init__(self):
        self._params = {}
        self._opts = []
        self._vars = []

    def update(self, other: 'CallMatch') -> None:
        self._params.update(other._params)
        self._opts += other._opts
        self._vars += other._vars

    def append_opt(self, present: bool) -> None:
        self._opts.append(present)

    def opt(self, index: int) -> bool:
        return self._opts[index]

    def append_var(self, variant: int) -> None:
        self._vars.append(variant)

    def var(self, index: int) -> int:
        return self._vars[index]

    def __getitem__(self, index):
        return self._params[index] if index in self._params else None

    def __setitem__(self, index, value):
        self._params[index] = value

    def __str__(self) -> str:
        return f'params: {self._params}, optionals: {self._opts}, variants: {self._vars}'
