from typing import List, Optional
from .node import Leaf
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class Parameter(Leaf):
    """A command parameter.

    Any token present in place of the parameter will be stored as the value
    of that parameter in the match.

    Parameters may also specify types that will be checked upon matching.
    """

    node_name = 'parameter'

    def __init__(self, name: str, typename: Optional[str] = None):
        """Initializes a parameter node.

        Parameters
        ----------
          * name: `str` - The name of the parameter.
          * typename: `str` (optional) - The name of the type to parse. Defaults to string.
        """

        super().__init__()
        self.name = name
        self.typename = typename

    def __str__(self) -> str:
        if self.typename is None:
            return f'<{self.name}>'
        else:
            return f'<{self.name}: {self.typename}>'

    def __repr__(self) -> str:
        return f'param {repr(self.name)}'

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) < 1:
            raise CallMatchFail(f'Expected argument for parameter <{self.name}>')

        # Type construction
        if self.typename is not None:
            typ = matcher.get_type(self.typename)
            try:
                value = typ(tokens[0].value)
            except ValueError:
                raise CallMatchFail(f"Argument {tokens[0]} for parameter <{self.name}> \
does not match type {self.typename}")

        # Type defaults to string
        else:
            value = tokens[0].value

        match.score += 1
        match.params[self.name] = value
        return tokens[1:]
