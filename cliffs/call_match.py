from typing import Any, List, Dict, Optional


class CallMatchFail(Exception):
    """
    Raised by syntax tree nodes when matching fails in an expected way,
    i.e. if a recursive parser call signals failed parsing to an upper parser,
    but also returned to the top-level caller if the root parser fails.
    """


class CallMatch:
    """Stores the result of a command call matched against a command syntax."""

    def __init__(self, raw: str):
        """Constructs a call match to be populated by the syntax tree recursive
        parsers.

        Parameters
        ----------
          * raw: `str` - The original call string passed to the lexer for tokenization.
        """

        self.raw = raw

        # Whether to prevent further matches from being performed under this match
        self.terminated = False
        # The original list of tokens given to the top-level match
        self.tokens = None  # type: Optional[List[str]]
        # The score for this match branch
        self.score = 0

        # Matched and parsed parameters
        self._params = {}  # type: Dict[str, Any]
        # Optional sequence matches
        self._opts = []  # type: List[bool]
        # Variant group matches
        self._vars = []  # type: List[int]

    def __str__(self) -> str:
        return f'params: {self._params}, optionals: {self._opts}, variants: {self._vars}'

    def join(self, other: 'CallMatch') -> None:
        """Collects the values populated to the given branched match into this match.

        Parameters
        ----------
          * other: `CallMatch` - The match to assimilate into this match.
        """

        self.terminated |= other.terminated
        self.score += other.score
        self._params.update(other._params)
        self._opts += other._opts
        self._vars += other._vars

    def branch(self) -> 'CallMatch':
        """Creates a copy of this call match for recursive matching.

        Returns
        -------
          * `CallMatch`: The copied call match.
        """

        match = CallMatch(self.raw)
        return match

    def __getitem__(self, index) -> Any:
        return self._params[index]

    def optional(self, n: int) -> bool:
        """Returns a bool indicating the presence of an optional sequence with
        the given index"""
        return self._opts[n]

    def variant(self, n: int) -> int:
        """Returns the index of the present variant in a variant group with
        the given index"""
        return self._vars[n]

    def __setitem__(self, index, value):
        self._params[index] = value

    def add_optional(self, present: bool):
        """Adds a bool indicating the presence of an optional sequence"""
        self._opts.append(present)

    def add_variant(self, index: int):
        """Adds the index of the present variant of a variant group"""
        self._vars.append(index)
