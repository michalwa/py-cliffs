from typing import List, Iterable, Callable, Optional
from .call_match import CallMatcher, CallMatch, CallMatchFail


class StLeaf:
    node_name = 'leaf'

    def __init__(self):
        self.parent = None  # type: Optional[StBranch]

    def debug(self) -> str:
        return self.node_name

    def traverse(self, callback: Callable[['StLeaf'], None]) -> None:
        callback(self)

    def iter_traverse(self) -> Iterable['StLeaf']:
        yield self

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        return tokens

    def match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        if match.terminated:
            raise SyntaxError(f"Tried matching {self.node_name} after matching was terminated")
        return self._match_call(tokens, matcher, match)


class StBranch(StLeaf):
    node_name = 'branch'

    def __init__(self):
        super().__init__()
        self.children = []  # type: List[StLeaf]

    def debug(self) -> str:
        return f'{self.node_name}[' + ', '.join(child.debug() for child in self.children) + ']'

    def append_child(self, child: StLeaf) -> 'StBranch':
        self.children.append(child)
        child.parent = self
        return self

    @property
    def last_child(self) -> Optional[StLeaf]:
        return self.children[-1] if len(self.children) > 0 else None

    def traverse(self, callback: Callable[[StLeaf], None]) -> None:
        callback(self)
        for child in self.children:
            child.traverse(callback)

    def iter_traverse(self) -> Iterable[StLeaf]:
        yield self
        for child in self.children:
            for leaf in child.iter_traverse():
                yield leaf

    def num_children(self) -> int:
        return len(self.children)


# Mixin class for any branch that can be assigned an identifier
class StIdentifiable:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identifier = None  # type: Optional[str]


class StLiteral(StLeaf):
    node_name = 'literal'

    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.value

    def debug(self) -> str:
        return f'literal("{self.value}")'

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        if len(tokens) < 1 or not matcher.compare_literal(tokens[0], self.value):
            raise CallMatchFail(f'Literal "{self.value}" not present')

        match.score += 1
        return tokens[1:]


class StParam(StLeaf):
    node_name = 'param'

    def __init__(self, name: str, typename: Optional[str] = None):
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


class StSequence(StBranch):
    node_name = 'sequence'

    def __str__(self) -> str:
        return ' '.join(str(child) for child in self.children)

    def _match_call(self, tokens: List[str], matcher: CallMatcher, match: CallMatch) -> List[str]:
        for child in self.children:
            tokens = child.match_call(tokens, matcher, match)
        return tokens


class StOptSequence(StIdentifiable, StBranch):
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


class StVarGroup(StIdentifiable, StBranch):
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
