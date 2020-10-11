from .node import Leaf
from ..call_match import *
from ..call_matcher import CallMatcher


class MissingTail(CallMatchFail):
    def __init__(self, expected: 'Tail'):
        super().__init__(f"Expected {expected.name}...")
        self.expected = expected


class Tail(Leaf):
    """A tail parameter.

    Similar to varargs but will store tokens as raw text as they were entered
    by the user/issuer (will keep whitespace).
    """

    node_name = 'tail'

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) \
            and self.name == other.name

    def __str__(self) -> str:
        return f"<{self.name}...>"

    def __repr__(self) -> str:
        return f'tail {repr(self.name)}'

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        if not match.has_tokens():
            raise MissingTail(self)

        else:
            text = match.raw[match.tokens[0].start:match.tokens[-1].end]
            if text == '':
                raise MissingTail(self)

            match[self.name] = text

        match.terminate()
