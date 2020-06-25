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
    _eq_exclude = []
    _copy_attrs = ['parent', 'inherited_identifier']

    def __init__(self):
        super().__init__()

        # Whether this variant group must be wrapped in parentheses
        self.wrapped = True

        # Whether the identifier for this group was inherited from the parent node
        self.inherited_identifier = False

    def append_child(self, child: Node) -> Node:
        if not isinstance(child, Variant):
            raise ValueError('Variant group children must be of type Variant')
        return super().append_child(child)

    def insert_child(self, index: int, child: Node) -> Node:
        if not isinstance(child, Variant):
            raise ValueError('Variant group children must be of type Variant')
        return super().insert_child(index, child)

    def __str__(self) -> str:
        children = '|'.join(str(child) for child in self.children)
        return f'({children})' if self.wrapped else children

    def flattened(self) -> Node:
        if self.num_children == 1:
            return self.last_child.as_plain_sequence()
        else:
            flat = super().flattened()

            # Decide whether the variant group should have parentheses around it:
            #
            # Wrap in parentheses if there is a parent and this group isn't its only child
            # or if this group has an identifier assigned that is not inherited from its parent
            flat.wrapped = flat.parent is not None and flat.parent.num_children != 1\
                or flat.identifier is not None and not flat.inherited_identifier

            # Unpack nested variant groups
            for variant in list(flat.children):
                if variant.num_children == 1 and isinstance(variant.last_child, VariantGroup)\
                        and not variant.last_child.wrapped:

                    i = flat.child_index(variant)
                    flat.remove_child(variant)
                    for subvariant in variant.last_child.children:
                        flat.insert_child(i, subvariant)
                        i += 1

            return flat

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
