from typing import List
from .node import Leaf
from ..token import Token
from ..call_match import CallMatch, CallMatcher


class Tail(Leaf):
    """A tail parameter.

    A tail parameter collects all leftover tokens (thus it must be the last node
    in any syntax specification; nodes matched after a tail are not allowed).
    """

    node_name = 'tail'

    def __init__(self, name: str):
        super().__init__()
        self.name = name

        # Whether to capture untokenized plaintext under the tail parameter
        self.raw = False

    def __str__(self) -> str:
        return f"<{self.name}...>"

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if self.raw:
            if len(tokens) == 0:
                match.params[self.name] = ''
            else:
                match.params[self.name] = match.raw[tokens[0].start:tokens[-1].end]
        else:
            match.params[self.name] = [token.value for token in tokens]

        match.terminated = True  # Disallow further elements to be matched
        return []
