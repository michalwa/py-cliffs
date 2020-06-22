from typing import Any, Iterable


class Token:
    """An atomic piece of information in a string of code."""

    def __init__(self, typ: str, raw: str, start: int, end: int, *, value: Any = None):
        """Initializes a generic token

        Parameters
        ----------
          * typ: `str` - A value indicating the type of the token.
          * value: `*` - The raw contents of the substring used to construct this token.
          * start: `int` - The starting index (inclusive) of the substring used to construct this token.
          * len: `int` - The end index (exclusive) of the substring used to construct this token.
          * value: `*` - A custom value to attach to this token.
        """

        self.typ = typ
        self.value = value or raw
        self.raw = raw
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f"{self.typ} {repr(self.value)} at {self.start}"

    def __repr__(self) -> str:
        return f"Token({self.typ}: {repr(self.value)} at {self.start}..{self.end})"
