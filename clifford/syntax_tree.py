from typing import Any, List, Iterable, Callable, Optional
from .call_match import CallMatcher, CallMatch, CallMatchFail


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

    @property
    def last_child(self) -> Optional['StNode']:
        return self.children[-1] if len(self.children) > 0 else None

    def append_child(self, child: 'StNode') -> 'StNode':
        self.children.append(child)
        child.parent = self
        return self

    def num_children(self) -> int:
        return len(self.children)

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

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        """This method is proxied by `match_call` which does additional checks
        before passing to this method. Refer to the documentation of `match_call`
        for more information.
        """
        return tokens

    def match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        """Tries to parse the given call tokens into the given match instance.

        Parameters
        ----------
          * tokens: `List[str]` - The tokens to parse.
          * matcher: `CallMatcher` - The matcher to use.
          * match: `CallMatch` - The match to populate.

        Returns
        -------
          * `List[str]`: The tokens left for further matching by other nodes.
        """

        if match.terminated:
            raise SyntaxError(f"Tried matching {self.node_name} after matching was terminated")
        return self._match_call(tokens, matcher, match)


class StLeaf(StNode):
    """A node that cannot have children"""

    def append_child(self, child: 'StNode') -> 'StNode':
        raise ValueError(f"Node of type {self.node_name} cannot have children")


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

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        if len(tokens) < 1 or not matcher.match_literal(self.value, tokens[0]):
            raise CallMatchFail(f'Literal "{self.value}" not present')

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

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        if len(tokens) < 1:
            raise CallMatchFail(f'Parameter <{self.name}> not present')

        if self.typename is not None:
            constr = matcher.get_type(self.typename)
            try:
                value = constr(tokens[0])
            except ValueError:
                raise CallMatchFail(f"Argument '{tokens[0]}' for parameter '{self.name}' \
does not match type '{self.typename}'")

        # Type defaults to string
        else:
            value = tokens[0]

        match.score += 1
        match.params[self.name] = value
        return tokens[1:]


class StSequence(StNode):
    """A simple sequence of syntax nodes.

    For a sequence to be matched by tokens, all child nodes must be matched.
    """

    node_name = 'sequence'

    def __str__(self) -> str:
        return ' '.join(str(child) for child in self.children)

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        for child in self.children:
            tokens = child.match_call(tokens, matcher, match)
        return tokens


class StOptSequence(StIdentifiable, StNode):
    """An optional sequence.

    An optional sequence will attempt to match its child nodes against the call,
    but will not interrupt parsing if it doesn't succeed.
    """

    node_name = 'opt_sequence'

    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        tokens_temp = tokens
        match_temp = CallMatch()
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

    def __init__(self):
        super().__init__()

    def append_child(self, child):
        if not isinstance(child, StSequence):
            raise ValueError('Variant group children must be of type StSequence')
        return super().append_child(child)

    def __str__(self) -> str:
        children = '|'.join(str(child) for child in self.children)
        return f"({children})"

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        for index, variant in enumerate(self.children):
            match_temp = CallMatch()
            try:
                tokens_temp = variant.match_call(tokens, matcher, match_temp)

                if self.identifier is not None:
                    match.params[self.identifier] = index
                else:
                    match.vars.append(index)

                match.update(match_temp)
                return tokens_temp
            except CallMatchFail:
                pass

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

    def __str__(self) -> str:
        return f"<{self.name}...>"

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        match.params[self.name] = tokens
        match.terminated = True  # Disallow further elements to be matched
        return []
