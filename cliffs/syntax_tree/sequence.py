from typing import List
from .node import StNode
from ..token import Token
from ..call_match import CallMatch, CallMatcher


class StSequence(StNode):
    """A simple sequence of syntax nodes.

    For a sequence to be matched by tokens, all child nodes must be matched.
    """

    node_name = 'sequence'

    def __str__(self) -> str:
        s = ' '.join(str(child) for child in self.children)
        return f'({s})' if self.parent is not None and self.parent.node_name != 'var_group' else s

    def __eq__(self, other) -> bool:
        if self.num_children == 1 and other == self.last_child:
            return True
        else:
            return super().__eq__(other)

    def flattened(self) -> str:
        if self.num_children == 1:
            return self.last_child.flattened()
        else:
            # Unpack nested sequences
            flat = super().flattened()
            new = StSequence()
            for child in flat.children:
                if isinstance(child, StSequence):
                    new.children += child.children
                else:
                    new.children.append(child)
            return new

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        for child in self.children:
            tokens = child.match_call(tokens, matcher, match)
        return tokens
