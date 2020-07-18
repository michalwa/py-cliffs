from typing import Any, Optional


class Token:
    """An atomic piece of information in a string of code."""

    def __init__(self, typ: Optional[str], raw: str, start: int, end: int, *, value: Any = None):
        """Initializes a generic token

        Parameters
        ----------
          * typ: `str` - A value indicating the type of the token.
          * value: `*` - The raw contents of the substring used to construct this token.
          * start: `int` - The starting index (inclusive) of the substring used to construct this token.
          * len: `int` - The end index (exclusive) of the substring used to construct this token.
          * value: `*` - A custom value to attach to this token.
        """

        self.type = typ
        self.value = value or raw
        self.raw = raw
        self.start = start
        self.end = end

    def __str__(self) -> str:
        if self.type is not None:
            return f"{self.type} {repr(self.value)} at {self.start}"
        else:
            return f"{repr(self.value)} at {self.start}"

    def __repr__(self) -> str:
        if self.type is not None:
            return f"Token({self.type}: {repr(self.value)} at {self.start}..{self.end})"
        else:
            return f"Token({repr(self.value)} at {self.start}..{self.end})"
