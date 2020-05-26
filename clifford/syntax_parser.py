from typing import Iterable, Tuple
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

            # Literals
            if token_type == 'literal':

                # Literals also serve as parameter names
                if state == 'PARAM_NAME':
                    if param_name is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    param_name = token_value

                # ...parameter types
                elif state == 'PARAM_TYPE':
                    if param_type is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    param_type = token_value

                # ...and group identifiers
                elif state == 'IDENTIFIER':
                    current.last_child.identifier = symbols.register(token_value)
                    state = 'NORMAL'

                # Regular literal
                else:
                    current.append_child(StLiteral(token_value))

            elif token_type == 'delim':

                # Opening parameter delimiter
                if token_value == '<':
                    if state != 'NORMAL':
                        raise SyntaxError("Unexpected parameter opening delimiter '<'")
                    state = 'PARAM_NAME'

                # Parameter type specifier separator,
                # Group identifier separator
                elif token_value == ':':
                    if state == 'PARAM_NAME' and param_name is not None:
                        state = 'PARAM_TYPE'
                    elif state == 'NORMAL' and hasattr(current.last_child, 'identifier'):
                        state = 'IDENTIFIER'
                    else:
                        raise SyntaxError("Unexpected separator ':'")

                # Closing parameter delimiter
                elif token_value == '>':
                    if state != 'PARAM_NAME' and state != 'PARAM_TYPE':
                        raise SyntaxError("Unexpected parameter closing delimiter '>'")
                    if param_name is None:
                        raise SyntaxError('Empty parameter name')

                    current.append_child(StParam(symbols.register(param_name), param_type))
                    param_name = None
                    param_type = None
                    state = 'NORMAL'

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

                    current = current.parent.parent

        # Check for unterminated expressions
        if current is not root:
            path = current.node_name
            while current.parent is not root:
                current = current.parent
                path = f'{current.node_name} > {path}'
            raise SyntaxError(f'Unterminated expression: {path}')

        return root
