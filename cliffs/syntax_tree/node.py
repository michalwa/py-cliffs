from typing import List, Optional, Iterable
from ..token import Token
from ..call_match import CallMatch, CallMatcher


class Node:
    """A node in a syntax tree"""

    node_name = 'node'

    # Attributes to exclude in equality comparison
    _eq_exclude = []  # type: List[str]

    # Attributes to pass to __init__ when copying
    _init_attrs = []  # type: List[str]

    # Attributes to include when copying
    _copy_attrs = ['parent']  # type: List[str]

    def __init__(self):
        self.parent = None  # type: Optional[Node]
        self.children = []  # type: List[Node]
        self._eq_exclude += ['parent', 'children']

    def __repr__(self) -> str:
        r = f'{self.node_name}'
        if self.children != []:
            r += '[' + ', '.join(repr(child) for child in self.children) + ']'
        return r

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        self_items = dict(self.__dict__)
        other_items = dict(other.__dict__)

        for item in self._eq_exclude:
            self_items.pop(item, 0)
            other_items.pop(item, 0)

        return self_items == other_items and self.children == other.children

    def __neq__(self, other) -> bool:
        return not self == other

    def __contains__(self, other) -> bool:
        """Returns True if the given object is a descendant of this node."""

        return other in self.children or any(other in child for child in self.children)

    @property
    def last_child(self) -> Optional['Node']:
        return self.children[-1] if len(self.children) > 0 else None

    @property
    def num_children(self) -> int:
        return len(self.children)

    def append_child(self, child: 'Node') -> 'Node':
        self.children.append(child)
        child.parent = self
        return self

    def remove_child(self, child: 'Node') -> 'Node':
        self.children.remove(child)
        child.parent = None
        return self

    def child_index(self, child: 'Node') -> int:
        return self.children.index(child)

    def insert_child(self, index: int, child: 'Node') -> 'Node':
        self.children.insert(index, child)
        return self

    def traverse(self) -> Iterable['Node']:
        """Recursively constructs an iterator that will traverse the descendants
        of this node (including this node itself).

        Returns
        ------
          * `Iterable[SyntaxNode]`: This node and its descendants.
        """

        yield self
        for child in self.children:
            for leaf in child.iter_traverse():
                yield leaf

    def flattened(self) -> 'Node':
        """Recusively creates a flattened copy of this node with minimized number
        of levels of descendants.
        """

        new = self.__class__(*(self.__getattribute__(k) for k in self._init_attrs))
        for k, v in self.__dict__.items():
            if k in self._copy_attrs:
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


class Leaf(Node):
    """A node that cannot have children"""

    def append_child(self, child: Node) -> Node:
        raise ValueError(f"Node of type {self.node_name} cannot have children")

    def insert_child(self, index: int, child: Node) -> Node:
        raise ValueError(f"Node of type {self.node_name} cannot have children")
