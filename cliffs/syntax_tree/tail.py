from typing import List
from .node import Leaf
from ..token import Token
from ..call_match import *


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

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) == 0:
            raise TokensExhaustedError(f"Expected {self.name}...")
        else:
            text = match.raw[tokens[0].start:tokens[-1].end]
            if text == '':
                raise CallMatchFail(f"Expected {self.name}...")
            match.params[self.name] = text

        match.terminated = True  # Disallow further elements to be matched
        return []
