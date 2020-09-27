from typing import List
from .node import Node
from ..token import Token
from ..call_match import CallMatch
from ..call_matcher import CallMatcher


class Sequence(Node):
    """A simple sequence of syntax nodes.

    For a sequence to be matched by tokens, all child nodes must be matched.
    """

    node_name = 'sequence'

    def __str__(self) -> str:
        # Render root sequence without parentheses
        s = ' '.join(str(child) for child in self.children)
        return f'({s})' if self.parent is not None else s

    def flattened(self) -> str:
        if self.num_children == 1:
            return self.nth_child(0).flattened()
        else:
            # Unpack nested sequences
            flat = super().flattened()
            new = Sequence()
            for child in flat.children:
                if isinstance(child, Sequence):
                    new.children += child.children
                else:
                    new.children.append(child)

            return new

    def match(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        tokens = super().match(tokens, matcher, match)

        for child in self.children:
            tokens = child.match(tokens, matcher, match)
        return tokens

    def expected_info(self) -> str:
        return self.nth_child(0).expected_info()
