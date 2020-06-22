from typing import Any, List, Dict, Optional, Callable
from .utils import loose_bool


class CallMatchFail(Exception):
    """Raised by syntax tree nodes when matching fails in an expected way,
    i.e. if a recursive parser call signals failed parsing to an upper parser,
    but also returned to the top-level caller if the root parser fails.
    """


class CallMatcher:
    """Aids in the process of matching a command call to a parsed command structure.
    Stores configuration parameters regulating how the tokens are matched and
    manages registered parameter types.
    """

    def __init__(self, case_sensitive: bool = True):
        """Initializes a matcher.

        Parameters
        ----------
          * case_sensitive: `bool` (optional) - Whether to use case-sensitive
            comparison when matching literals. Defaults to True.
        """

        self._types = {}  # type: Dict[str, Callable[[str], Any]]

        self.case_sensitive = case_sensitive

        self.register_type(str)
        self.register_type(int)
        self.register_type(float)
        self.register_type(loose_bool, 'bool')

    def register_type(self, constructor: Callable[[str], Any], name: Optional[str] = None):
        """Registers the given type for matching parameter values.

        Parameters
        ----------
          * constructor: `(str) -> Any` - The constructor of the type from string.
          * name: `str` (optional) - The name of the type. Defaults to
            the `__name__` of the constructor.
        """

        if name is None:
            name = constructor.__name__
        self._types[name] = constructor

    def get_type(self, name: str) -> Callable[[str], Any]:
        """Returns the constructor of the specified type from string.

        Parameters
        ----------
          * name: `str` - The name of the type to return the constructor of.

        Returns
        -------
          * `(str) -> *`: The constructor.

        Raises
        ------
          * `SyntaxError` when the specified type is not defined.
        """

        if name not in self._types:
            raise SyntaxError(f"Undefined type '{name}'")
        return self._types[name]

    def match_literal(self, expected: str, actual: str) -> bool:
        """Matches a literal token.

        Parameters
        ----------
          * expected: `str` - The expected literal.
          * actual: `str` - The actual token to compare against the literal.

        Returns
        -------
          * `bool`: Whether the token matches the literal.
        """

        if self.case_sensitive:
            return expected == actual
        else:
            return expected.lower() == actual.lower()


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

        self.terminated = False

        self.tokens = None  # type: Optional[List[str]]
        self.score = 0
        self.params = {}  # type: Dict[str, Any]
        self.opts = []  # type: List[bool]
        self.vars = []  # type: List[int]
        self.tail = []  # type: List[str]

    def update(self, other: 'CallMatch') -> None:
        """Pushes the values appended to the given match to this match instance.

        Parameters
        ----------
          * other: `CallMatch` - The match to assimilate into this match.
        """

        self.terminated |= other.terminated
        self.score += other.score
        self.params.update(other.params)
        self.opts += other.opts
        self.vars += other.vars

    def branch(self) -> 'CallMatch':
        """Creates a copy of this call match for recursive matching.

        Returns
        -------
          * `CallMatch`: The copied call match.
        """

        match = CallMatch(self.raw)
        return match

    def __str__(self) -> str:
        return f'params: {self.params}, optionals: {self.opts}, variants: {self.vars}'
