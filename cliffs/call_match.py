from typing import Any, List, Dict, Optional
from .token import Token


class CallMatchFail(Exception):
    """
    Raised by syntax tree nodes to signal failed parsing to an upper node,
    returned to the top-level caller if parsing fails.
    """


class CallMatch:
    """Stores the result of a command call matched entirely or partially
    against a command syntax."""

    def __init__(self, raw: str, tokens: List[Token]):
        """Constructs a call match to be populated by the syntax tree recursive
        parsers.

        Parameters
        ----------
          * raw: `str` - The raw command issued.
          * tokens: `List[Token]` - The tokens left to be matched.
        """

        # The raw command issued passed to the top-level match
        self.raw = raw
        # The tokens left to be matched
        self.tokens = tokens  # type: List[Token]
        # The score for this match branch
        self.score = 0
        # Whether to prevent further matches from being performed under this match
        self.terminated = False
        # Matched and parsed parameters
        self._params = {}  # type: Dict[str, Any]
        # Optional sequence matches
        self._opts = []  # type: List[bool]
        # Variant group matches
        self._vars = []  # type: List[int]

        self.hint = None  # type: Optional[str]

    def __repr__(self) -> str:
        return f'<CallMatch params={self._params}, optionals={self._opts}, variants={self._vars}>'

    def fork(self) -> 'CallMatch':
        """Creates a fork of this match that can be passed to child nodes for matching
        and then joined back into this match with the `+=` operator.

        Returns
        -------
          * `CallMatch`: The forked match
        """
        return CallMatch(self.raw, self.tokens)

    def __iadd__(self, other: 'CallMatch') -> 'CallMatch':
        self.tokens = other.tokens
        self.score += other.score
        self.terminated |= other.terminated
        self._params.update(other._params)
        self._opts += other._opts
        self._vars += other._vars
        return self

    def has_tokens(self, num: int = 1) -> bool:
        """Returns true if the number of tokens left to be matched is at least
        the specified number."""
        return len(self.tokens) >= num

    def take_tokens(self, num: int) -> List[Token]:
        """Removes a specified number of tokens from the start of the token list
        and return them

        Parameters
        ----------
          * num: `int` - The number of tokens to remove.
        """
        taken, self.tokens = self.tokens[:num], self.tokens[num:]
        return taken

    def terminate(self):
        """Removes all tokens from the token list and marks the match as terminated"""
        self.tokens = []
        self.terminated = True

    def __getitem__(self, index) -> Any:
        return self._params[index]

    def __setitem__(self, index, value):
        self._params[index] = value

    def optional(self, n: int) -> bool:
        """Returns a bool indicating the presence of an optional sequence with
        the given index"""
        return self._opts[n]

    def add_optional(self, present: bool):
        """Adds a bool indicating the presence of an optional sequence"""
        self._opts.append(present)

    def variant(self, n: int) -> int:
        """Returns the index of the present variant in a variant group with
        the given index"""
        return self._vars[n]

    def add_variant(self, index: int):
        """Adds the index of the present variant of a variant group"""
        self._vars.append(index)
