from typing import Iterable, Tuple
from .syntax_tree import *

class SyntaxParser:
    def parse(self, tokens: Iterable[Tuple[str, str]]) -> StBranch:
        root = StSequence()
        current = root  # type: StBranch

        for token_type, token_value in tokens:

            # Literals & params
            if token_type == 'literal':
                current.append_child(StLiteral(token_value))
            elif token_type == 'param':
                current.append_child(StParam(token_value))

            elif token_type == 'delim':

                # Opening optional sequence delimiter
                if token_value == '[':
                    child = StOptSequence()  # type: StBranch
                    current.append_child(child)
                    current = child

                # Closing optional sequence delimiter
                elif token_value == ']':
                    if not isinstance(current, StOptSequence):
                        raise SyntaxError("Unmatched optional sequence closing delimiter ']'")
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
