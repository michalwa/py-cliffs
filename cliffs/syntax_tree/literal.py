from difflib import SequenceMatcher
from .node import Leaf
from ..call_match import *
from ..call_matcher import CallMatcher
from ..token import Token


class MissingLiteral(CallMatchFail):
    def __init__(self, expected: 'Literal'):
        super().__init__(f"Expected literal {repr(expected.value)}")
        self.expected = expected


class MismatchedLiteral(CallMatchFail):
    def __init__(self, expected: 'Literal', actual: Token, suggest: bool = False):
        if suggest:
            super().__init__(f"Probably meant {repr(expected.value)}, got {actual}")
        else:
            super().__init__(f"Expected literal {repr(expected.value)}, got {actual}")

        self.suggest = suggest
        self.expected = expected
        self.actual = actual


class Literal(Leaf):
    """A literal command token.

    A token **must** be present in the command call to match a literal.
    """

    node_name = 'literal'

    def __init__(self, value: str, *, case_sensitive: bool = True, tolerant: bool = False):
        """Initializes a literal node.

        Parameters
        ----------
          * value: `str` - The contents of the literal.
          * case_sensitive: `bool` - Whether the literal should be matched respecting
            letter case (defaults to `True`)
          * tolerant: `bool` - Whether the literal should match successfully when
            match ratio is below the threshold configured in the `CallMatcher`.
            By default, a suggestive exception will be raised.
        """

        super().__init__()
        self.value = value
        self.case_sensitive = case_sensitive
        self.tolerant = tolerant

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

        ratio = self.compare(match.tokens[0].value)

        if ratio != 1.0:
            if ratio >= matcher.literal_threshold:
                match.score += 0.25

                if self.tolerant:
                    match.take_tokens(1)
                    return

                raise MismatchedLiteral(self, match.tokens[0], True)
            else:
                raise MismatchedLiteral(self, match.tokens[0])

        match.score += 1
        match.take_tokens(1)

    def compare(self, string: str) -> float:
        """
        Returns a similarity metric (0.0 - 1.0) based on how similar the value
        of this literal is to the given string.
        """

        value = self.value

        if not self.case_sensitive:
            string = string.lower()
            value = value.lower()

        if value == string:
            return 1.0
        else:
            return SequenceMatcher(None, value, string).ratio()

    def expected_info(self) -> str:
        return repr(self.value)
