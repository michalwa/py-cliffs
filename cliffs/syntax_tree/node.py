import inspect
from typing import Optional
from ..call_match import CallMatch
from ..call_matcher import CallMatcher


class Node:
    """A node in a syntax tree"""

    node_name = 'node'

    def __init__(self):
        self.parent: Optional[Node] = None
        self.children: list[Node] = []

    def __repr__(self) -> str:
        r = f'{self.node_name}'
        if self.children != []:
            r += '[' + ', '.join(repr(child) for child in self.children) + ']'
        return r

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) \
            and self.children == other.children

    def __neq__(self, other) -> bool:
        return not self == other

    def __contains__(self, other) -> bool:
        """Returns True if the given object is a descendant of this node."""

        return other in self.children or any(other in child for child in self.children)

    def nth_child(self, n: int) -> Optional['Node']:
        try:
            return self.children[n]
        except IndexError:
            return None

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

    def flattened(self) -> 'Node':
        """Recusively creates a flattened copy of this node with minimized number
        of levels of descendants.
        """

        # Find attributes that need to be passed to __init__
        init_sig = inspect.signature(self.__class__.__init__)
        args = []
        kwargs = {}
        for name, param in init_sig.parameters.items():
            if name != 'self':
                if param.kind == param.POSITIONAL_ONLY:
                    args.append(self.__getattribute__(name))
                elif param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
                    kwargs[name] = self.__getattribute__(name)

        new = self.__class__(*args, **kwargs)

        for child in self.children:
            new.append_child(child.flattened())

        return new

    def match(self, match: CallMatch, matcher: CallMatcher):
        """Tries to match the leftover tokens in the given match against the syntax
        of this node. The passed match is mutated for this purpose - results
        are appended, score is incremented, etc. and tokens are removed off the
        start of the list.

        Parameters
        ----------
          * match: `CallMatch` - The match to continue.
          * matcher: `CallMatcher` - The matcher providing context for the match.

        Returns
        -------
          * `CallMatch`: The resulting match.

        Raises
        ------
          * `SyntaxError` when matching fails because of malformed command syntax.
          * `CallMatchFail` when matching fails and should be terminated.
        """

        if match.terminated:
            raise SyntaxError(f"Tried matching {self.node_name} after match was terminated")

    def expected_info(self) -> str:
        return str(self)


class Leaf(Node):
    """A node that cannot have children"""

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__)

    def append_child(self, child: Node) -> Node:
        raise ValueError(f"Node of type {self.node_name} cannot have children")

    def insert_child(self, index: int, child: Node) -> Node:
        raise ValueError(f"Node of type {self.node_name} cannot have children")
