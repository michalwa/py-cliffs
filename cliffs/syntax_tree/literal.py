from typing import List
from .node import Leaf
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class Literal(Leaf):
    """A literal command token.

    A token **must** be present in the command call to match a literal.
    """

    node_name = 'literal'
    _init_attrs = ['value']

    def __init__(self, value: str):
        """Initializes a literal node.

        Parameters
        ----------
          * value: `str` - The contents of the literal.
        """

        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'literal {repr(self.value)}'

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) < 1:
            raise CallMatchFail(f"Expected literal '{self.value}'")
        if not matcher.match_literal(self.value, tokens[0].value):
            raise CallMatchFail(f"Expected literal '{self.value}', got {tokens[0]}")

        match.score += 1
        return tokens[1:]
