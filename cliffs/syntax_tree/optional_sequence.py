from .node import Node
from .identifiable import Identifiable
from ..call_match import *
from ..call_matcher import CallMatcher


class OptionalSequence(Identifiable, Node):
    """An optional sequence.

    An optional sequence will attempt to match its child nodes against the call,
    but will not interrupt parsing if it doesn't succeed.
    """

    node_name = 'optional_sequence'

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def match(self, match: CallMatch, matcher: CallMatcher):
        super().match(match, matcher)

        fork = match.fork()

        for child in self.children:
            try:
                child.match(fork, matcher)

            except CallMatchFail as fail:
                if self.identifier is not None:
                    match[self.identifier] = False
                else:
                    match.add_optional(False)

                match.score += fork.score
                match.hint = str(fail)
                return

        if self.identifier is not None:
            match[self.identifier] = True
        else:
            match.add_optional(True)

        match += fork
