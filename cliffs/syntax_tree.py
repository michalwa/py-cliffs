from typing import Any, List, Iterable, Callable, Optional
from itertools import permutations
from .call_match import CallMatcher, CallMatch, CallMatchFail
from .token import Token


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


class StIdentifiable:
    """Mixin class for any node that can be assigned an identifier"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identifier = None  # type: Optional[str]


class StLiteral(StLeaf):
    """A literal command token.

    A token **must** be present in the command call to match a literal.
    """

    node_name = 'literal'

    def __init__(self, value: str):
        """Initializes a literal node.

        Parameters
        ----------
          * value: `str` - The contents of the literal.
        """

        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.value

    def debug(self) -> str:
        return f'literal("{self.value}")'

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) < 1:
            raise CallMatchFail(f"Expected literal '{self.value}'")
        if not matcher.match_literal(self.value, tokens[0].value):
            raise CallMatchFail(f"Expected literal '{self.value}', got {tokens[0]}")

        match.score += 1
        return tokens[1:]


class StParam(StLeaf):
    """A command parameter.

    Any token present in place of the parameter will be stored as the value
    of that parameter in the match.

    Parameters may also specify types that will be checked upon matching.
    """

    node_name = 'param'

    def __init__(self, name: str, typename: Optional[str] = None):
        """Initializes a parameter node.

        Parameters
        ----------
          * name: `str` - The name of the parameter.
          * typename: `str` (optional) - The name of the type to parse. Defaults to string.
        """

        super().__init__()
        self.name = name
        self.typename = typename

    def __str__(self) -> str:
        if self.typename is None:
            return f'<{self.name}>'
        else:
            return f'<{self.name}: {self.typename}>'

    def debug(self) -> str:
        return f'param("{self.name}")'

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if len(tokens) < 1:
            raise CallMatchFail(f'Expected argument for parameter <{self.name}>')

        # Type construction
        if self.typename is not None:
            typ = matcher.get_type(self.typename)
            try:
                value = typ(tokens[0].value)
            except ValueError:
                raise CallMatchFail(f"Argument {tokens[0]} for parameter <{self.name}> \
does not match type {self.typename}")

        # Type defaults to string
        else:
            value = tokens[0].value

        match.score += 1
        match.params[self.name] = value
        return tokens[1:]


class StSequence(StNode):
    """A simple sequence of syntax nodes.

    For a sequence to be matched by tokens, all child nodes must be matched.
    """

    node_name = 'sequence'

    def __str__(self) -> str:
        s = ' '.join(str(child) for child in self.children)
        return f'({s})' if self.parent is not None and not isinstance(self.parent, StVarGroup) else s

    def __eq__(self, other) -> bool:
        if self.num_children == 1 and other == self.last_child:
            return True
        else:
            return super().__eq__(other)

    def flattened(self) -> str:
        if self.num_children == 1:
            return self.last_child.flattened()
        else:
            # Unpack nested sequences
            flat = super().flattened()
            new = StSequence()
            for child in flat.children:
                if isinstance(child, StSequence):
                    new.children += child.children
                else:
                    new.children.append(child)
            return new

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        for child in self.children:
            tokens = child.match_call(tokens, matcher, match)
        return tokens


class StOptSequence(StIdentifiable, StNode):
    """An optional sequence.

    An optional sequence will attempt to match its child nodes against the call,
    but will not interrupt parsing if it doesn't succeed.
    """

    node_name = 'opt_sequence'

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        tokens_temp = tokens
        match_temp = match.branch()
        for child in self.children:
            try:
                tokens_temp = child.match_call(tokens_temp, matcher, match_temp)
            except CallMatchFail:
                if self.identifier is not None:
                    match.params[self.identifier] = False
                else:
                    match.opts.append(False)

                return tokens

        if self.identifier is not None:
            match.params[self.identifier] = True
        else:
            match.opts.append(True)

        match.update(match_temp)
        return tokens_temp


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


class StTail(StLeaf):
    """A tail parameter.

    A tail parameter collects all leftover tokens (thus it must be the last node
    in any syntax specification; nodes matched after a tail are not allowed).
    """

    node_name = 'tail'

    def __init__(self, name: str):
        super().__init__()
        self.name = name

        # Whether to capture untokenized plaintext under the tail parameter
        self.raw = False

    def __str__(self) -> str:
        return f"<{self.name}...>"

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:
        if self.raw:
            if len(tokens) == 0:
                match.params[self.name] = ''
            else:
                match.params[self.name] = match.raw[tokens[0].start:tokens[-1].end]
        else:
            match.params[self.name] = [token.value for token in tokens]

        match.terminated = True  # Disallow further elements to be matched
        return []


class StUnordered(StNode):
    """An unordered group.

    Children of this group can be matched in an arbitrary order.
    """

    node_name = 'unordered'

    def __str__(self) -> str:
        return f"{{{' '.join(str(child) for child in self.children)}}}"

    def flattened(self) -> StNode:
        if self.num_children == 1:
            return self.last_child.flattened()
        else:
            return super().flattened()

    def _match_call(self, tokens: List[Token], matcher: CallMatcher, match: CallMatch) -> List[Token]:

        first_fail = None
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
                if first_fail is None:
                    first_fail = fail

        # Choose best scoring match
        if matches != []:
            best_match, tokens = sorted(matches, key=lambda m: m[0].score, reverse=True)[0]
            match.update(best_match)
            return tokens

        # If there was no successful permutation found, fail
        else:
            if first_fail is not None:
                raise first_fail
            else:
                raise CallMatchFail('Unmatched unordered group')
