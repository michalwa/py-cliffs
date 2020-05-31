from typing import cast, Iterable, Tuple
from .syntax_tree import *


class SymbolList:
    def __init__(self):
        self.symbols = []

    def register(self, symbol: str) -> str:
        if symbol in self.symbols:
            raise SyntaxError(f"Symbol '{symbol}' used more than once")
        self.symbols.append(symbol)
        return symbol


class SyntaxParser:
    def parse(self, tokens: Iterable[Tuple[str, str]]) -> StBranch:
        root = StSequence()
        current = root  # type: StBranch

        symbols = SymbolList()

        state = 'NORMAL'
        param_name = None
        param_type = None

        for token_type, token_value in tokens:

            # Symbols
            if token_type == 'symbol':

                # Parameter names
                if state == 'BEFORE_PARAM_NAME':
                    if param_name is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    param_name = token_value
                    state = 'AFTER_PARAM_NAME'

                # Parameter types
                elif state == 'BEFORE_PARAM_TYPE':
                    if param_type is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    param_type = token_value
                    state = 'AFTER_PARAM_TYPE'

                # Group identifiers
                elif state == 'BEFORE_IDENTIFIER':
                    group = cast(StIdentifiable, current.last_child)
                    group.identifier = symbols.register(token_value)
                    state = 'NORMAL'

                # Literals
                else:
                    current.append_child(StLiteral(token_value))

            # Tail ellipsis
            elif token_type == 'ellipsis':
                if state != 'AFTER_PARAM_NAME' or param_name is None:
                    raise SyntaxError("Unexpected ellipsis '...'")

                current.append_child(StTail(param_name))
                state = 'AFTER_TAIL'

            elif token_type == 'delim':

                # Opening parameter delimiter
                if token_value == '<':
                    if state != 'NORMAL':
                        raise SyntaxError("Unexpected parameter opening delimiter '<'")
                    state = 'BEFORE_PARAM_NAME'

                elif token_value == ':':

                    # Parameter type specifier separator,
                    if state == 'AFTER_PARAM_NAME':
                        state = 'BEFORE_PARAM_TYPE'

                    # Group identifier separator
                    elif state == 'NORMAL' and isinstance(current.last_child, StIdentifiable):
                        state = 'BEFORE_IDENTIFIER'

                    else:
                        raise SyntaxError("Unexpected separator ':'")

                elif token_value == '>':

                    # Closing parameter delimiter
                    if state in ['AFTER_PARAM_NAME', 'AFTER_PARAM_TYPE']:
                        if param_name is None:
                            raise SyntaxError('Empty parameter name')

                        current.append_child(StParam(symbols.register(param_name), param_type))
                        param_name = None
                        param_type = None
                        state = 'NORMAL'

                    # Closing tail parameter delimiter
                    elif state == 'AFTER_TAIL':
                        pass

                    else:
                        raise SyntaxError("Unexpected parameter closing delimiter '>'")

                # Opening optional sequence delimiter
                elif token_value == '[':
                    if state != 'NORMAL':
                        raise SyntaxError("Unexpected optional sequence opening delimiter '['")

                    child = StOptSequence()  # type: StBranch
                    current.append_child(child)
                    current = child

                # Closing optional sequence delimiter
                elif token_value == ']':
                    if state != 'NORMAL' or not isinstance(current, StOptSequence):
                        raise SyntaxError("Unexpected optional sequence closing delimiter ']'")
                    if current.num_children() == 0:
                        raise SyntaxError('Empty optional sequence')

                    if current.parent is not None:
                        current = current.parent

                # Opening variant group delimiter
                elif token_value == '(':
                    if state != 'NORMAL':
                        raise SyntaxError("Unexpected variant group opening delimiter '('")

                    child = StVarGroup()
                    grandchild = StSequence()
                    child.append_child(grandchild)
                    current.append_child(child)
                    current = grandchild

                # Variant group sequence separator
                elif token_value == '|':
                    if state != 'NORMAL' or not isinstance(current, StSequence) or not isinstance(current.parent, StVarGroup):
                        raise SyntaxError("Unexpected variant separator '|'")
                    if current.num_children() == 0:
                        raise SyntaxError('Empty variant')

                    current = current.parent
                    child = StSequence()
                    current.append_child(child)
                    current = child

                # Closing variant group delimiter
                elif token_value == ')':
                    if state != 'NORMAL' and not isinstance(current, StSequence) or not isinstance(current.parent, StVarGroup):
                        raise SyntaxError("Unexpected variant group closing delimiter ')'")
                    if current.num_children() == 0:
                        raise SyntaxError('Empty variant')

                    if current.parent is not None and current.parent.parent is not None:
                        current = current.parent.parent

        # Check for unterminated expressions
        if current is not root:
            path = current.node_name
            while current.parent is not root and current.parent is not None:
                current = current.parent
                path = f'{current.node_name} > {path}'
            raise SyntaxError(f'Unterminated expression: {path}')

        return root
