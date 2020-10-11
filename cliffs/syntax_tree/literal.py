from .node import Leaf
from ..call_match import *
from ..call_matcher import CallMatcher
from ..token import Token


class MissingLiteral(CallMatchFail):
    def __init__(self, expected: 'Literal'):
        super().__init__(f"Expected literal {repr(expected.value)}")
        self.expected = expected


class MismatchedLiteral(CallMatchFail):
    def __init__(self, expected: 'Literal', actual: Token):
        super().__init__(f"Expected literal {repr(expected.value)}, got {actual}")
        self.expected = expected
        self.actual = actual


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

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        if not match.has_tokens():
            raise MissingLiteral(self)
        if not self.compare(match.tokens[0].value):
            raise MismatchedLiteral(self, match.tokens[0])

        match.score += 1
        match.take_tokens(1)

    def compare(self, string: str) -> bool:
        """Checks if the given string matches this literal."""

        if self.case_sensitive:
            return self.value == string
        else:
            return self.value.lower() == string.lower()

    def expected_info(self) -> str:
        return repr(self.value)
