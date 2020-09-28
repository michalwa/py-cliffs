from typing import List, Tuple
from .node import Node
from ..token import Token
from ..utils import best
from ..call_match import *
from ..call_matcher import CallMatcher


class UnorderedGroup(Node):
    """An unordered group.

    Children of this group can be matched in an arbitrary order.
    """

    node_name = 'unordered_group'

    def __str__(self) -> str:
        return '{' + ' '.join(str(child) for child in self.children) + '}'

    def flattened(self) -> Node:
        if self.num_children == 1:
            return self.nth_child(0).flattened()
        else:
            return super().flattened()

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        unused = list(self.children)

        # Try to find a matching order until the unused children are exhausted
        while unused != []:
            matches = []  # type: List[Tuple[Node, CallMatch]]
            fails = []  # type: List[Tuple[CallMatchFail, int]]

            # Collect matches from all unused children
            for child in unused:
                fork = match.fork()
                try:
                    child.match(fork, matcher)
                    matches.append((child, fork))
                except CallMatchFail as fail:
                    if fork.score > 0:
                        fails.append((fail, fork.score))

            # Find the best and append it to the global list
            if matches != []:
                child, best_match = best(matches, lambda m: m[1].score)
                match += best_match
                unused.remove(child)

            # If no unused child matched during an iteration, fail
            elif fails != []:
                best_fail, best_fail_score = best(fails, lambda f: f[1])
                match.score += best_fail_score
                raise best_fail

            # If there is no appropriate fail to raise, raise a generic fail
            else:
                expected_info = ' or '.join(set(child.expected_info() for child in unused))
                if match.tokens != []:
                    raise CallMatchFail(f"Expected {expected_info}, got {match.tokens[0]}")
                else:
                    raise CallMatchFail(f"Expected {expected_info}")

    def expected_info(self) -> str:
        return ' or '.join(set(child.expected_info() for child in self.children))
