from typing import Dict, Tuple, Callable
from .syntax_tree import StBranch
from .syntax_lexer import SyntaxLexer
from .syntax_parser import SyntaxParser
from .call_lexer import CallLexer
from .call_match import CallMatch, CallMatchError


# typedefs
CommandCallback = Callable[[CallMatch], None]
CommandCallbackDecorator = Callable[[CommandCallback], CommandCallback]


class CommandDispatcher:
    def __init__(self, stx_lexer=SyntaxLexer(), stx_parser=SyntaxParser(), call_lexer=CallLexer()):
        self._commands = {}  # type: Dict[str, Tuple[StBranch, CommandCallback]]
        self._stx_lexer = stx_lexer
        self._stx_parser = stx_parser
        self._call_lexer = call_lexer

    def register(self, prefix: str, syntax: StBranch, callback: CommandCallback) -> None:
        self._commands[prefix] = syntax, callback

    def command(self, syntax: str) -> CommandCallbackDecorator:
        prefix, syntax = syntax.split(maxsplit=1)
        st_root = self._stx_parser.parse(self._stx_lexer.tokenize(syntax))
        def decorator(f: CommandCallback) -> CommandCallback:
            self.register(prefix, st_root, f)
            return f
        return decorator

    def dispatch(self, command: str) -> bool:
        tokens = list(self._call_lexer.tokenize(command))

        if len(tokens) == 0:
            return False

        prefix, tokens = tokens[0], tokens[1:]

        if not prefix in self._commands:
            return False

        call_match = CallMatch()
        left = self._commands[prefix][0].match_call(tokens, call_match)

        if len(left) > 0:
            raise CallMatchError('Too many arguments')

        self._commands[prefix][1](call_match)

        return True
