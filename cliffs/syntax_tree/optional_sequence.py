from typing import List
from .node import Node
from .identifiable import Identifiable
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class OptionalSequence(Identifiable, Node):
    """An optional sequence.

    An optional sequence will attempt to match its child nodes against the call,
    but will not interrupt parsing if it doesn't succeed.
    """

    node_name = 'optional_sequence'

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        tokens_temp = tokens
        match_temp = match.branch()
        for child in self.children:
            try:
                tokens_temp = child.match_call(tokens_temp, matcher, match_temp)
            except CallMatchFail:
                if self.identifier is not None:
                    match.params[self.identifier] = False
                else:
                    match.opts.append(False)

                return tokens

        if self.identifier is not None:
            match.params[self.identifier] = True
        else:
            match.opts.append(True)

        match.update(match_temp)
        return tokens_temp
