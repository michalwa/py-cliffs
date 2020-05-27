from typing import List, Dict, Optional, Callable
from .utils import loose_bool


# typedef
StrConstructor = Callable[[str], object]


class CallMatchFail(Exception):
    """Raised by syntax tree nodes when matching fails in an expected way"""


class CallMatcher:
    def __init__(self, case_sensitive: bool = True):
        self._types = {}  # type: Dict[str, StrConstructor]

        self.case_sensitive = case_sensitive
        
        self.register_type(str)
        self.register_type(int)
        self.register_type(float)
        self.register_type(loose_bool, 'bool')

    def register_type(self, constructor: StrConstructor, name: Optional[str] = None):
        if name is None:
            name = constructor.__name__
        self._types[name] = constructor

    def get_type(self, name: str) -> StrConstructor:
        if not name in self._types:
            raise SyntaxError(f"Undefined type '{name}'")
        return self._types[name]

    def compare_literal(self, a: str, b: str) -> bool:
        if self.case_sensitive:
            return a == b
        else:
            return a.lower() == b.lower()


class CallMatch:
    def __init__(self):
        self.terminated = False

        self.tokens = None  # type: Optional[List[str]]
        self.score = 0
        self.params = {}  # type: Dict[str, object]
        self.opts = []  # type: List[bool]
        self.vars = []  # type: List[int]
        self.tail = []  # type: List[str]

    def update(self, other: 'CallMatch') -> None:
        self.terminated |= other.terminated
        self.score += other.score
        self.params.update(other.params)
        self.opts += other.opts
        self.vars += other.vars

    def __str__(self) -> str:
        return f'params: {self.params}, optionals: {self.opts}, variants: {self.vars}'
