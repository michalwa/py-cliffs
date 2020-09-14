from typing import List
from .node import Leaf
from ..token import Token
from ..call_match import *


class Literal(Leaf):
    """A literal command token.

    A token **must** be present in the command call to match a literal.
    """

    node_name = 'literal'

    def __init__(self, value: str, *, case_sensitive: bool = True):
        """Initializes a literal node.

        Parameters
        ----------
          * value: `str` - The contents of the literal.
        """

        super().__init__()
        self.value = value
        self.case_sensitive = case_sensitive

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) \
            and self.value == other.value \
            and self.case_sensitive == other.case_sensitive

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'literal {repr(self.value)}'

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) < 1:
            raise TokensExhaustedError(f"Expected literal '{self.value}'")
        if not self.match(tokens[0].value):
            raise CallMatchFail(f"Expected literal '{self.value}', got {tokens[0]}")

        match.score += 1
        return tokens[1:]

    def match(self, string: str) -> bool:
        """Checks if the given string matches this literal."""

        if self.case_sensitive:
            return self.value == string
        else:
            return self.value.lower() == string.lower()

    def expected_info(self) -> str:
        return f"'{self.value}'"
