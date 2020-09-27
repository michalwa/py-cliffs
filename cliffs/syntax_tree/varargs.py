from typing import List
from .node import Leaf
from ..token import Token
from ..call_match import CallMatch
from ..call_matcher import CallMatcher


# TODO: Make varargs comma-separated

class VarArgs(Leaf):
    """Variadic argument parameter

    Collects all leftover tokens (must be the last, right-most node in any syntax
    specification; nodes matched after a tail are not allowed).
    """

    node_name = 'varargs'

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) \
            and self.name == other.name

    def __str__(self) -> str:
        return f"<{self.name}*>"

    def __repr__(self) -> str:
        return f'varargs {repr(self.name)}'

    def match(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        tokens = super().match(tokens, matcher, match)

        match[self.name] = [token.value for token in tokens]
        match.terminated = True  # Disallow further elements to be matched
        return []
