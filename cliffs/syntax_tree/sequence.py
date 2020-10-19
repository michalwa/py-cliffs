from .node import Node
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

    def flattened(self) -> Node:
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

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        for child in self.children:
            child.match(match, matcher)

    def expected_info(self) -> str:
        return self.nth_child(0).expected_info()
