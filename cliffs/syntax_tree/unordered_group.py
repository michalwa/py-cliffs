from typing import List, Tuple
from .node import Node
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail
from ..utils import best


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

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:

        best_matches = []
        score = 0
        unused = list(self.children)

        # Try to find a matching order until the unused children are exhausted
        while unused != []:
            matches = []  # type: List[Tuple[CallMatch, List[Token]]]
            fails = []  # type: List[Tuple[CallMatchFail, int]]

            # Collect matches from all unused children
            for child in unused:
                submatch = match.branch()
                try:
                    left_tokens = child.match_call(tokens, matcher, submatch)
                    matches.append((child, submatch, left_tokens))
                except CallMatchFail as fail:
                    if submatch.score > 0:
                        fails.append((fail, submatch.score))

            # Find the best and append it to the global list
            if matches != []:
                child, best_match, tokens = best(matches, lambda m: m[1].score)
                best_matches.append(best_match)
                unused.remove(child)
                score += best_match.score

            # If no unused child matched during an iteration, fail
            elif fails != []:
                best_fail, best_fail_score = best(fails, lambda f: f[1])
                match.score += score + best_fail_score
                raise best_fail

            # If there is no appropriate fail to raise, raise a generic fail
            else:
                match.score += score

                expected_info = ' or '.join(set(child.expected_info() for child in unused))
                if tokens != []:
                    raise CallMatchFail(f"Expected {expected_info}, got {tokens[0]}")
                else:
                    raise CallMatchFail(f"Expected {expected_info}")

        # Collect matches from all iterations
        for best_match in best_matches:
            match.join(best_match)

        return tokens

    def expected_info(self) -> str:
        return ' or '.join(set(child.expected_info() for child in self.children))
