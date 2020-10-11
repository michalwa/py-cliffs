from .node import Leaf
from ..call_match import CallMatch
from ..call_matcher import CallMatcher


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

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        match[self.name] = [token.value for token in match.tokens]
        match.terminate()
