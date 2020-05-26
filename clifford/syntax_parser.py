from typing import Iterable, Tuple
from .syntax_tree import *

class SyntaxParser:
    def parse(self, tokens: Iterable[Tuple[str, str]]) -> StBranch:
        root = StSequence()
        current = root  # type: StBranch

        symbols = []

        state = 'NORMAL'
        param_name = None
        param_type = None

        for token_type, token_value in tokens:

            # Literals
            if token_type == 'literal':

                # Literals serve both as parameter names and type specifiers
                if state == 'PARAM_NAME':
                    if param_name is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    if param_name in symbols:
                        raise SyntaxError(f"Duplicate symbol '{param_name}'")
                    param_name = token_value
                    symbols.append(param_name)
                elif state == 'PARAM_TYPE':
                    if param_type is not None:
                        raise SyntaxError(f"Unexpected literal '{token_value}'")
                    param_type = token_value

                # Regular literal
                else:
                    current.append_child(StLiteral(token_value))

            elif token_type == 'delim':

                # Opening parameter delimiter
                if token_value == '<':
                    if state != 'NORMAL':
                        raise SyntaxError("Unexpected parameter opening delimiter '<'")
                    state = 'PARAM_NAME'

                # Parameter type specifier separator
                elif token_value == ':':
                    if state != 'PARAM_NAME' or param_name is None:
                        raise SyntaxError("Unexpected parameter type separator ':'")
                    state = 'PARAM_TYPE'

                # Closing parameter delimiter
                elif token_value == '>':
                    if state != 'PARAM_NAME' and state != 'PARAM_TYPE':
                        raise SyntaxError("Unexpected parameter closing delimiter '>'")
                    if param_name is None:
                        raise SyntaxError('Empty parameter name')

                    current.append_child(StParam(param_name, param_type))
                    param_name = None
                    param_type = None
                    state = 'NORMAL'

                # Opening optional sequence delimiter
                elif token_value == '[':
                    child = StOptSequence()  # type: StBranch
                    current.append_child(child)
                    current = child

                # Closing optional sequence delimiter
                elif token_value == ']':
                    if not isinstance(current, StOptSequence):
                        raise SyntaxError("Unexpected optional sequence closing delimiter ']'")
                    if current.num_children() == 0:
                        raise SyntaxError('Empty optional sequence')

                    current = current.parent

                # Opening variant group delimiter
                elif token_value == '(':
                    child = StVarGroup()
                    grandchild = StSequence()
                    child.append_child(grandchild)
                    current.append_child(child)
                    current = grandchild

                # Variant group sequence separator
                elif token_value == '|':
                    if not isinstance(current, StSequence) or not isinstance(current.parent, StVarGroup):
                        raise SyntaxError("Unexpected variant separator '|'")
                    if current.num_children() == 0:
                        raise SyntaxError('Empty variant')

                    current = current.parent
                    child = StSequence()
                    current.append_child(child)
                    current = child

                # Closing variant group delimiter
                elif token_value == ')':
                    if not isinstance(current, StSequence) or not isinstance(current.parent, StVarGroup):
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
