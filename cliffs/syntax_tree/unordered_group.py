from typing import List
from itertools import permutations
from .node import Node
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class UnorderedGroup(Node):
    """An unordered group.

    Children of this group can be matched in an arbitrary order.
    """

    node_name = 'unordered_group'

    def __str__(self) -> str:
        return f"{{{' '.join(str(child) for child in self.children)}}}"

    def flattened(self) -> Node:
        if self.num_children == 1:
            return self.last_child.flattened()
        else:
            return super().flattened()

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:

        best_fail = None
        best_score = 0
        matches = []

        for perm in permutations(self.children):
            match_temp = match.branch()
            tokens_temp = tokens
            try:
                for child in perm:
                    tokens_temp = child.match_call(tokens_temp, matcher, match_temp)

                # Match found
                matches.append((match_temp, tokens_temp))

            except CallMatchFail as fail:
                if match_temp.score > best_score:
                    best_fail = fail
                    best_score = match_temp.score

            finally:
                if match_temp.score > best_score:
                    best_score = match_temp.score

        # Add the final best score to the total match score
        match.score += best_score

        # Choose best scoring match
        if matches != []:
            best_match, tokens = sorted(matches, key=lambda m: m[0].score, reverse=True)[0]
            match.update(best_match)
            return tokens

        # If there was no successful permutation found, fail
        else:
            if best_fail is not None:
                raise best_fail
            else:
                raise CallMatchFail('Unmatched unordered group')
