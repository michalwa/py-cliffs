import logging
from .syntax_lexer import SyntaxLexer
from .syntax_tree import *
from .utils import instance_or_kwargs


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
        """Initializes a syntax parser.

        Keyword arguments
        -----------------
          * lexer: `SyntaxLexer` or `dict` - The lexer to use to tokenize strings before parsing.

          * simplify: `str`:
            - 'no': Parsed trees will not be simplified nor reported.
            - 'warn' (default): Parsed trees will be simplified and compared against non-simplified trees,
                which will be returned. Any possible simplification will be logged to the
                `cliffs.syntax_parser` logger as an info message.
            - 'yes': Parsed trees will be simplified. Any applied simplification
                will be logged to `cliffs.syntax_parser` as an info message.
            - 'silently': Parsed trees will be simplified without being reported.

          * symbol_list_class: `Type[SymbolList]` - The symbol list class to use when parsing.
            Defaults to SymbolList.
          * all_case_insensitive: `bool` - Whether to parse literals as case-insensitive by default.
        """

        self.simplify = kwargs['simplify_mode'] if 'simplify_mode' in kwargs\
            and kwargs['simplify_mode'] in ('no', 'warn', 'yes', 'silently') else 'warn'

        self.lexer = instance_or_kwargs(kwargs.get('lexer', {}), SyntaxLexer)

        self.symbol_list_class: type[SymbolList] = kwargs.get('symbol_list_class', SymbolList)
        self.all_case_insensitive: bool = kwargs.get('all_case_insensitive', False)

    def parse(self, string: str) -> Node:
        """Parses the given sequence of tokens into a syntax tree.

        Parameters
        ----------
          * string: `str` - The string to parse.

        Returns
        -------
          * `Node`: The root of the parsed syntax tree.

        Raises
        ------
          * `SyntaxError` when there is an error in the specification.
        """

        tokens = self.lexer.tokenize(string)

        root = Sequence()
        current: Node = root

        symbols = self.symbol_list_class()

        state = 'NORMAL'
        param_name = None
        param_type = None

        for token in tokens:

            # Symbols
            if token.type == 'symbol':

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
                    group = current.nth_child(-1)

                    # If assining identifier to a wrapper around a variant group, e.g. [a|b|c]:id
                    # The variant group should be identified instead of the parent group; as if it were [(a|b|c):id]
                    # unless the variant group had parentheses around it
                    if group.num_children == 1 and isinstance(group.nth_child(-1), VariantGroup) and\
                            not group.nth_child(-1).parentheses:

                        group.nth_child(-1).identifier = symbols.register(token.value)
                        group.nth_child(-1).inherited_identifier = True

                    else:
                        group.identifier = symbols.register(token.value)

                    state = 'NORMAL'

                # Literals
                else:
                    current.append_child(Literal(token.value))

                    if self.all_case_insensitive:
                        current.nth_child(-1).case_sensitive = False

            # Varargs asterisk
            elif token.value == '*':
                if state != 'AFTER_PARAM_NAME' or param_name is None:
                    raise SyntaxError(f"Unexpected {token}")

                current.append_child(VarArgs(param_name))
                state = 'PARAM_SKIP'

            # Tail ellipsis
            elif token.value == '...':
                if state != 'AFTER_PARAM_NAME' or param_name is None:
                    raise SyntaxError(f"Unexpected {token}")

                current.append_child(Tail(param_name))
                state = 'PARAM_SKIP'

            # Case-insensitive hat/caret
            elif token.value == '^':
                if state != 'NORMAL' or type(current.nth_child(-1)) is not Literal:
                    raise SyntaxError(f"Unexpected {token}")

                # TODO: Allow modifier on groups?

                current.nth_child(-1).case_sensitive = False

            # Tolerance modifier
            elif token.value == '~':
                if state != 'NORMAL' or type(current.nth_child(-1)) is not Literal:
                    raise SyntaxError(f"Unexpected {token}")

                # Allow modifier on groups?

                current.nth_child(-1).tolerant = True

            # Opening parameter delimiter
            elif token.value == '<':
                if state != 'NORMAL':
                    raise SyntaxError(f"Unexpected {token}")
                state = 'BEFORE_PARAM_NAME'

            elif token.value == ':':

                # Parameter type specifier separator,
                if state == 'AFTER_PARAM_NAME':
                    state = 'BEFORE_PARAM_TYPE'

                # Group identifier separator
                elif state == 'NORMAL':
                    if isinstance(current.nth_child(-1), Identifiable):
                        state = 'BEFORE_IDENTIFIER'
                    else:
                        raise SyntaxError(
                            f"Unexpected {token}: Cannot assign identifier "
                            f"to {current.nth_child(-1).node_name}")

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

                # Closing tail delimiter
                elif state == 'PARAM_SKIP':
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
                        raise SyntaxError(
                            f"Unexpected {token}: Cannot define variants "
                            f"in {current.node_name}, maybe you meant to use parentheses?")

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
                        current.remove_child(current.nth_child(-1))
                        current.append_child(group)
                    else:
                        # Replace all children of the current node with the variant group
                        group.parentheses = False
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
                    if not current.parent.parentheses:
                        raise SyntaxError(f"Unexpected {token}")
                    if current.num_children == 0:
                        raise SyntaxError(f"Unexpected {token}: Empty variant")

                    current = current.parent.parent

            # Opening optional sequence delimiter
            elif token.value == '[':
                if state != 'NORMAL':
                    raise SyntaxError(f"Unexpected {token}")

                child = OptionalSequence()
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
                        current.parent.parentheses,
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

            after_hat = False

        # Leave unterminated variant
        if isinstance(current, Variant):
            current = current.parent.parent

        # Check for unterminated expressions
        if current is not root:
            path = current.node_name
            while current.parent is not root and current.parent is not None:
                current = current.parent
                path = f'{current.node_name} > {path}'
            raise SyntaxError(f'Unterminated expression: {path}')

        # Finalize
        if self.simplify == 'no':
            return root

        else:
            # Manually flatten root sequence
            if root.num_children == 1:
                root = root.nth_child(-1)
                root.parent.remove_child(root)

            # Flatten recursively
            flat_root = root.flattened()

            if self.simplify == 'warn':
                if root != flat_root:
                    logging.getLogger('cliffs.syntax_parser').info(
                        'Syntax "%s" can be simplified to "%s"', root, flat_root)

                return root

            elif self.simplify == 'yes':
                if root != flat_root:
                    logging.getLogger('cliffs.syntax_parser').info(
                        'Syntax "%s" simplified to "%s"', root, flat_root)

                return flat_root

            elif self.simplify == 'silently':
                return flat_root

            else:
                raise ValueError(f"Unknown simplify mode: {self.simplify}")
