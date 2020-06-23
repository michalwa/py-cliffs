from typing import List
from .node import StNode
from .identifiable import StIdentifiable
from .sequence import StSequence
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class StVarGroup(StIdentifiable, StNode):
    """A variant group.

    A variant group contains variants (sequences) either of which must be matched
    for the group to successfully match.
    """

    node_name = 'var_group'

    def append_child(self, child):
        if not isinstance(child, StSequence):
            raise ValueError('Variant group children must be of type StSequence')
        return super().append_child(child)

    def __str__(self) -> str:
        children = '|'.join(str(child) for child in self.children)
        return f"({children})"

    def flattened(self) -> StNode:
        if self.num_children == 1:
            return self.last_child.flattened()
        else:
            # Only flatten variants
            new = StVarGroup()
            new.identifier = self.identifier
            new.children = [child.flattened() for child in self.children]
            return new

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        first_fail = None

        for index, variant in enumerate(self.children):
            match_temp = match.branch()
            try:
                tokens_temp = variant.match_call(tokens, matcher, match_temp)

                if self.identifier is not None:
                    match.params[self.identifier] = index
                else:
                    match.vars.append(index)

                match.update(match_temp)
                return tokens_temp

            except CallMatchFail as fail:
                if first_fail is None:
                    first_fail = fail

        if first_fail is not None:
            raise first_fail
        else:
            raise CallMatchFail('No variant present')
