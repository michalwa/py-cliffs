from typing import List
from .node import Node
from .identifiable import Identifiable
from .sequence import Sequence
from ..token import Token
from ..call_match import CallMatch, CallMatcher, CallMatchFail


class VariantGroup(Identifiable, Node):
    """A variant group.

    A variant group contains variants (sequences) either of which must be matched
    for the group to successfully match.
    """

    node_name = 'variant_group'
    _eq_exclude = ['wrapped']

    def __init__(self):
        super().__init__()

        # Whether this is a plain variant group in parentheses (False)
        # or whether it is wrapped in another structure (True)
        self.wrapped = False

    def append_child(self, child):
        if not isinstance(child, Variant):
            raise ValueError('Variant group children must be of type Variant')
        return super().append_child(child)

    def __str__(self) -> str:
        children = '|'.join(str(child) for child in self.children)
        return f'({children})' if not self.wrapped and self.parent is not None else children

    def flattened(self) -> Node:
        if self.num_children == 1:
            return self.last_child.as_plain_sequence()
        else:
            # Only flatten variants
            new = VariantGroup()
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


class Variant(Sequence):
    """A sequence that is one of the variants of a variant group."""

    node_name = 'variant'

    def __str__(self):
        return ' '.join(str(child) for child in self.children)

    def flattened(self):
        return Node.flattened(self)

    def as_plain_sequence(self) -> Sequence:
        seq = Sequence()
        seq.children = [child.flattened() for child in self.children]
        return seq
