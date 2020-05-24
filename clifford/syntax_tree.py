from typing import List, Callable, Optional, cast
from .call_match import CallMatch, CallMatchFail


class StLeaf:
    node_name = 'leaf'

    def __init__(self):
        self.parent = None

    def debug(self) -> str:
        return self.node_name

    def traverse(self, callback: Callable[['StLeaf'], None]) -> None:
        callback(self)

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        return expr


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

    def traverse(self, callback: Callable[[StLeaf], None]) -> None:
        callback(self)
        for child in self.children:
            child.traverse(callback)

    def num_children(self) -> int:
        return len(self.children)


class StLiteral(StLeaf):
    node_name = 'literal'

    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.value

    def debug(self) -> str:
        return f'literal("{self.value}")'

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        if len(expr) < 1 or expr[0] != self.value:
            raise CallMatchFail(f'Literal "{self.value}" not present')
        return expr[1:]


class StParam(StLeaf):
    node_name = 'param'

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __str__(self) -> str:
        return f'<{self.name}>'

    def debug(self) -> str:
        return f'param("{self.name}")'

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        if len(expr) < 1:
            raise CallMatchFail(f'Parameter <{self.name}> not present')
        call_match[self.name] = expr[0]
        return expr[1:]


class StSequence(StBranch):
    node_name = 'sequence'

    def __str__(self) -> str:
        return ' '.join(str(child) for child in self.children)

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        for child in self.children:
            expr = child.match_call(expr, call_match)
        return expr


class StOptSequence(StBranch):
    node_name = 'opt_sequence'

    def __str__(self) -> str:
        children = ' '.join(str(child) for child in self.children)
        return f"[{children}]"

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        expr_temp = expr
        call_match_temp = CallMatch()
        for child in self.children:
            try:
                expr_temp = child.match_call(expr_temp, call_match_temp)
            except CallMatchFail:
                call_match.append_opt(False)
                return expr

        call_match.append_opt(True)
        call_match.update(call_match_temp)
        return expr_temp


class StVarGroup(StBranch):
    node_name = 'var_group'

    def append_child(self, child):
        if not isinstance(child, StSequence):
            raise ValueError('Variant group children must be of type StSequence')
        return super().append_child(child)

    def __str__(self) -> str:
        children = '|'.join(str(child) for child in self.children)
        return f"({children})"

    def match_call(self, expr: List[str], call_match: CallMatch) -> List[str]:
        for index, variant in enumerate(self.children):
            call_match_temp = CallMatch()
            try:
                expr_temp = variant.match_call(expr, call_match_temp)
                call_match.append_var(index)
                call_match.update(call_match_temp)
                return expr_temp
            except CallMatchFail:
                pass
            
        raise CallMatchFail('No variant present')
