import logging
from typing import Type, Iterable
from .token import Token
from .syntax_tree import *


class SymbolList:
    """Manages symbols used in a command syntax specification."""

    def __init__(self):
        self.symbols = []

    def register(self, symbol: str) -> str:
        """Registers a symbol and returns the identifier to be used in place of
        the symbol (can just be the symbol itself).

        Parameters
        ----------
          * symbol: `str` - The symbol to register.

        Returns
        -------
          * `str`: The idenfier to use in place of the symbol.

        Raises
        ------
          * `SyntaxError` when the symbol has already been used or cannot be used
            for some other reason.
        """

        if symbol in self.symbols:
            raise SyntaxError(f"Symbol '{symbol}' used more than once")
        self.symbols.append(symbol)
        return symbol


class SyntaxParser:
    """Parses syntax specification strings into syntax trees which serve the
    function of recursive parsers for command calls."""

    def __init__(self, **kwargs):
        """Initializes a syntax specification parser.

        Keyword arguments
        -----------------
          * symbol_list_class: `Type[SymbolList]` - The symbol list class to use when parsing.
        """

        self.symbol_list_class = kwargs.get('symbol_list_class', SymbolList)  # type: Type[SymbolList]

    def parse(self, tokens: Iterable[Token]) -> Node:
        """Parses the given sequence of tokens into a syntax tree.

        Parameters
        ----------
          * tokens: `Iterable[Token]` - The tokens to parse.

        Returns
        -------
          * `Node`: The root of the parsed syntax tree.

        Raises
        ------
          * `SyntaxError` when there is an error in the specification.
        """

        root = Sequence()
        current = root  # type: Node

        symbols = self.symbol_list_class()

        state = 'NORMAL'
        param_name = None
        param_type = None

        for token in tokens:

            # Symbols
            if token.typ == 'symbol':

                # Parameter names
                if state == 'BEFORE_PARAM_NAME':
                    param_name = token.value
                    state = 'AFTER_PARAM_NAME'

                # Parameter types
                elif state == 'BEFORE_PARAM_TYPE':
                    param_type = token.value
                    state = 'AFTER_PARAM_TYPE'

                # Group identifiers
                elif state == 'BEFORE_IDENTIFIER':
                    group = current.last_child
                    group.identifier = symbols.register(token.value)
                    state = 'NORMAL'

                # Literals
                else:
                    current.append_child(Literal(token.value))

            # Tail ellipsis
            elif token.typ == 'ellipsis':
                if state != 'AFTER_PARAM_NAME' or param_name is None:
                    raise SyntaxError(f"Unexpected {token}")

                current.append_child(Tail(param_name))
                state = 'AFTER_TAIL'

            elif token.typ == 'asterisk':
                if state != 'AFTER_TAIL':
                    raise SyntaxError(f"Unexpected {token}")

                current.last_child.raw = True
                state = 'AFTER_TAIL_RAW'

            elif token.typ == 'delimeter':

                # Opening parameter delimiter
                if token.value == '<':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")
                    state = 'BEFORE_PARAM_NAME'

                elif token.value == ':':

                    # Parameter type specifier separator,
                    if state == 'AFTER_PARAM_NAME':
                        state = 'BEFORE_PARAM_TYPE'

                    # Group identifier separator
                    elif state == 'NORMAL' and isinstance(current.last_child, Identifiable):
                        state = 'BEFORE_IDENTIFIER'

                    else:
                        raise SyntaxError(f"Unexpected {token}")

                elif token.value == '>':

                    # Closing parameter delimiter
                    if state in ['AFTER_PARAM_NAME', 'AFTER_PARAM_TYPE']:
                        if param_name is None:
                            raise SyntaxError('Empty parameter name')

                        current.append_child(Parameter(symbols.register(param_name), param_type))
                        param_name = None
                        param_type = None
                        state = 'NORMAL'

                    # Closing tail parameter delimiter
                    elif state in ['AFTER_TAIL', 'AFTER_TAIL_RAW']:
                        state = 'NORMAL'

                    else:
                        raise SyntaxError(f"Unexpected {token}")

                # Variant separator
                elif token.value == '|':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    if current.num_children == 0:
                        raise SyntaxError(f"Unexpected {token}: Empty variant")

                    if isinstance(current, Variant):
                        # Construct a new variant and make it the current scope
                        current = current.parent
                        new_variant = Variant()
                        current.append_child(new_variant)
                        current = new_variant

                    else:
                        if not isinstance(current, (Sequence, OptionalSequence)):
                            raise SyntaxError(f"Unexpected {token}: Cannot define variants \
in {current.node_name}, maybe use parentheses?")

                        # Convert the current node into a variant
                        variant = Variant()
                        for child in current.children:
                            variant.append_child(child)
                        current.children = []

                        # Create a variant group and append the current variant to it
                        group = VariantGroup()
                        group.append_child(variant)

                        if isinstance(current, Sequence) and current.parent is not None:
                            # If this is the root node or something other than a plain sequence,
                            # replace the entire sequence with the variant group
                            current = current.parent
                            current.remove_child(current.last_child)
                            current.append_child(group)
                        else:
                            # Replace all children of the current node with the variant group
                            group.wrapped = True
                            current.append_child(group)

                        # Construct a new variant and make it the current scope
                        new_variant = Variant()
                        group.append_child(new_variant)
                        current = new_variant

                # Opening sequence delimiter
                elif token.value == '(':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    child = Sequence()
                    current.append_child(child)
                    current = child

                # Closing sequence delimiter
                elif token.value == ')':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    if not isinstance(current, Variant):
                        if not isinstance(current, Sequence):
                            raise SyntaxError(f"Unexpected {token}")
                        if current.num_children == 0:
                            raise SyntaxError(f"Unexpected {token}: Empty sequence")

                        current = current.parent

                    else:
                        if current.parent.wrapped:
                            raise SyntaxError(f"Unexpected {token}")
                        if current.num_children == 0:
                            raise SyntaxError(f"Unexpected {token}: Empty variant")

                        current = current.parent.parent

                # Opening optional sequence delimiter
                elif token.value == '[':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    child = OptionalSequence()  # type: StNode
                    current.append_child(child)
                    current = child

                # Closing optional sequence delimiter
                elif token.value == ']':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    if not isinstance(current, Variant):
                        if not isinstance(current, OptionalSequence):
                            raise SyntaxError(f"Unexpected {token}")
                        if current.num_children == 0:
                            raise SyntaxError(f"Unexpected {token}: Empty optional sequence")

                        current = current.parent

                    else:
                        if any([
                            not current.parent.wrapped,
                            not isinstance(current.parent.parent, OptionalSequence)
                        ]):
                            raise SyntaxError(f"Unexpected {token}")
                        if current.num_children == 0:
                            raise SyntaxError(f"Unexpected {token}: Empty variant")

                        current = current.parent.parent.parent

                # Unordered group delimiter
                elif token.value == '{':
                    if state != 'NORMAL':
                        raise SyntaxError(f"Unexpected {token}")

                    child = UnorderedGroup()
                    current.append_child(child)
                    current = child

                # Unordered group delimiter
                elif token.value == '}':
                    if any([
                        state != 'NORMAL',
                        not isinstance(current, UnorderedGroup),
                    ]):
                        raise SyntaxError(f"Unexpected {token}")

                    if current.num_children == 0:
                        raise SyntaxError(f"Unexpected {token}: Empty unordered group")

                    current = current.parent

                else:
                    raise SyntaxError(f"Unknown token: {token}")

        # Leave unterminated variants
        while isinstance(current, Variant):
            current = current.parent.parent

        # Check for unterminated expressions
        if current is not root:
            path = current.node_name
            while current.parent is not root and current.parent is not None:
                current = current.parent
                path = f'{current.node_name} > {path}'
            raise SyntaxError(f'Unterminated expression: {path}')

        # Manually flatten root sequence
        if root.num_children == 1:
            root = root.last_child
            root.parent.remove_child(root)

        # Flatten
        flat_root = root.flattened()

        if root != flat_root:
            logging.getLogger('cliffs.syntax_parser').info(
                'Syntax "%s" can be simplified to "%s"', root, flat_root)

        return flat_root
