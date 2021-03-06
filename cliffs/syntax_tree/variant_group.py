from .node import Node
from .identifiable import Identifiable
from .sequence import Sequence
from ..utils import best
from ..call_match import *
from ..call_matcher import CallMatcher


class MissingVariant(CallMatchFail):
    def __init__(self, expected: 'VariantGroup'):
        super().__init__(f"Expected {expected.expected_info()}")
        self.expected = expected


class NoMatchedVariant(CallMatchFail):
    def __init__(self, expected: 'VariantGroup', actual: Token):
        super().__init__(f"Expected {expected.expected_info()}, got {actual}")
        self.expected = expected
        self.actual = actual


class VariantGroup(Identifiable, Node):
    """A variant group.

    A variant group contains variants (sequences) either of which must be matched
    for the group to successfully match.
    """

    node_name = 'variant_group'

    def __init__(self):
        super().__init__()

        # Whether this variant group must be wrapped in parentheses
        self.parentheses = True

        # Whether the identifier for this group was inherited from the parent node
        self.inherited_identifier = False

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.parentheses == other.parentheses \
            and self.children == other.children

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
        return f'({children})' if self.parentheses else children

    def flattened(self) -> Node:
        if self.num_children == 1:
            return self.nth_child(0).flattened()
        else:
            flat = super().flattened()
            flat.inherited_identifier = self.inherited_identifier

            # Decide whether the variant group should have parentheses around it:
            #
            # Wrap in parentheses if there is a parent and this group isn't its only child
            # or if this group has an identifier assigned that is not inherited from its parent
            flat.parentheses = self.parent is not None and self.parent.num_children != 1\
                or flat.identifier is not None and not flat.inherited_identifier

            # Unpack nested variant groups
            for variant in list(flat.children):
                if variant.num_children == 1 and isinstance(variant.nth_child(-1), VariantGroup)\
                        and not variant.nth_child(-1).parentheses:

                    i = flat.child_index(variant)
                    flat.remove_child(variant)
                    for subvariant in variant.nth_child(-1).children:
                        flat.insert_child(i, subvariant)
                        i += 1

            return flat

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        matches: list[tuple[int, CallMatch]] = []
        fails: list[tuple[CallMatchFail, int]] = []

        # Iterate through variants collecting:
        # - matches in tuples: (index, match)
        # - non-0-scoring fails (CallMatchFail) in tuples: (fail, score)
        for index, variant in enumerate(self.children):
            fork = match.fork()

            try:
                variant.match(fork, matcher)
                matches.append((index, fork))

            except CallMatchFail as fail:
                if fork.score > 0:
                    fails.append((fail, fork.score))

        # If a best match exists...
        if matches != []:
            # ...find it...
            best_index, best_match = best(matches, lambda m: m[1].score)

            # ...append its index to the match...
            if self.identifier is not None:
                best_match[self.identifier] = best_index
            else:
                best_match.add_variant(best_index)

            # ...update the super-match and return leftover tokens
            match += best_match

        # If the best fail exists, raise it
        elif fails != []:
            best_fail, best_score = best(fails, lambda f: f[1])
            match.score += best_score
            raise best_fail

        # Raise the default fail otherwise
        elif match.tokens != []:
            raise NoMatchedVariant(self, match.tokens[0])
        else:
            raise MissingVariant(self)

    def expected_info(self) -> str:
        return ' or '.join(set(variant.expected_info() for variant in self.children))


class Variant(Sequence):
    """A sequence that is one of the variants of a variant group."""

    node_name = 'variant'

    def __str__(self):
        return ' '.join(str(child) for child in self.children)

    def flattened(self) -> Node:
        if self.num_children == 1 and isinstance(self.nth_child(0), Sequence):
            new = Variant()
            for child in self.nth_child(0).children:
                new.append_child(child)

            return new

        return self
