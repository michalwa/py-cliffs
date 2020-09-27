from typing import Any, Dict, Optional, Callable
from .utils import loose_bool


class CallMatcher:
    """
    Provides context in the process of matching a command call against a parsed
    command syntax. Stores configuration parameters regulating how the tokens
    are matched and manages registered parameter types.
    """

    def __init__(self):
        """Initializes a matcher"""

        self._types = {}  # type: Dict[str, Callable[[str], Any]]

        self.register_type(str)
        self.register_type(int)
        self.register_type(float)
        self.register_type(loose_bool, 'bool')

    def register_type(self, constructor: Callable[[str], Any], name: Optional[str] = None):
        """Registers the given type for matching parameter values.

        Parameters
        ----------
          * constructor: `str -> *` - The constructor of the type from string.
          * name: `str` (optional) - The name of the type. Defaults to
            the `__name__` of the constructor.
        """

        name = name or constructor.__name__
        self._types[name] = constructor

    def parse_arg(self, typename: str, value: str) -> Any:
        """Parses the given string using a registered type with the given name.

        Parameters
        ----------
          * typename: `str` - The name of the type to parse.
          * value: `str` - The value to parse.

        Returns
        -------
          * `Any`: The parsed value

        Raises
        ------
          * `SyntaxError` if there is no registered type with the given name
          * `ValueError` if the type constructor raises `ValueError`
        """

        if typename not in self._types:
            raise SyntaxError(f"Undefined type {repr(typename)}")

        return self._types[typename](value)
