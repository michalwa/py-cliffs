from typing import List, Optional, Iterable, Callable, Any
from ..token import Token
from ..call_match import CallMatch, CallMatcher


class StNode:
    """A node in a syntax tree"""

    node_name = 'node'

    def __init__(self):
        self.parent = None  # type: Optional[StNode]
        self.children = []  # type: List[StNode]

    def __repr__(self) -> str:
        r = f'{self.node_name}'
        if self.children != []:
            r += '[' + ', '.join(repr(child) for child in self.children) + ']'
        return r

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        self_items = dict(self.__dict__)
        self_items.pop('parent', 0)
        other_items = dict(other.__dict__)
        other_items.pop('parent', 0)

        return self_items == other_items and self.children == other.children

    def __neq__(self, other) -> bool:
        return not self == other

    @property
    def last_child(self) -> Optional['StNode']:
        return self.children[-1] if len(self.children) > 0 else None

    @property
    def num_children(self) -> int:
        return len(self.children)

    def append_child(self, child: 'StNode') -> 'StNode':
        self.children.append(child)
        child.parent = self
        return self

    def remove_child(self, child: 'StNode') -> 'StNode':
        self.children.remove(child)
        child.parent = None
        return self

    def traverse(self, callback: Callable[['StNode'], Any]) -> None:
        """Recursively traverses the descendants of the node calling the callback
        with each individual descendant (including this node itself).

        Parameters
        ----------
          * callback: `(StNode) -> *` - The callback to call with each descendant.
        """

        callback(self)
        for child in self.children:
            child.traverse(callback)

    def iter_traverse(self) -> Iterable['StNode']:
        """Recursively constructs an iterator that will traverse the descendants
        of this node (including this node itself).

        Returns
        ------
          * `Iterable[StNode]`: This node and its descendants.
        """

        yield self
        for child in self.children:
            for leaf in child.iter_traverse():
                yield leaf

    def flattened(self) -> 'StNode':
        """Creates a flattened version (not necessarily copy) of this node with
        minimized number of generations of descendants.
        """

        new = self.__class__()
        for k, v in self.__dict__.items():
            if k != 'children':
                new.__setattr__(k, v)

        for child in self.children:
            new.append_child(child.flattened())
        return new

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        """This method is proxied by `match_call` which does additional checks
        before passing to this method. Refer to the documentation of `match_call`
        for more information.
        """
        return tokens

    def match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        """Tries to parse the given call tokens into the given match instance.

        Parameters
        ----------
          * tokens: `List[Token]` - The tokens to parse.
          * matcher: `CallMatcher` - The matcher to use.
          * match: `CallMatch` - The match to populate.

        Returns
        -------
          * `List[Token]`: The tokens left for further matching by other nodes.
        """

        if match.terminated:
            raise SyntaxError(f"Tried matching {self.node_name} after matching was terminated")
        return self._match_call(tokens, matcher, match)


class StLeaf(StNode):
    """A node that cannot have children"""

    def append_child(self, child: StNode) -> StNode:
        raise ValueError(f"Node of type {self.node_name} cannot have children")

    def flattened(self) -> StNode:
        return self
