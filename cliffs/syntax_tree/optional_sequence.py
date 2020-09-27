from typing import List
from .node import Node
from .identifiable import Identifiable
from ..token import Token
from ..call_match import *
from ..call_matcher import CallMatcher


class OptionalSequence(Identifiable, Node):
    """An optional sequence.

    An optional sequence will attempt to match its child nodes against the call,
    but will not interrupt parsing if it doesn't succeed.
    """

    node_name = 'optional_sequence'

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def match(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        tokens = super().match(tokens, matcher, match)

        tokens_temp = tokens
        match_temp = match.branch()

        for child in self.children:
            try:
                tokens_temp = child.match(tokens_temp, matcher, match_temp)

            except CallMatchFail as f:

                # NOTE (FIXME): This causes some issues if there are multiple sibling optional
                # sequences starting with the same literal or with other nodes that match the same
                # token, but I have no better idea how to implement this at the moment.

                # TODO: Maybe check unmatched optional sequences from "above"?

                # If some tokens matched, raise fail
                if match_temp.score > 0:
                    match.join(match_temp)
                    raise f

                if self.identifier is not None:
                    match[self.identifier] = False
                else:
                    match.add_optional(False)

                return tokens

        if self.identifier is not None:
            match[self.identifier] = True
        else:
            match.add_optional(True)

        match.join(match_temp)
        return tokens_temp
