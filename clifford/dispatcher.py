from typing import TypeVar, Dict, List, Iterable, Tuple, Callable, Any
from itertools import chain
from .syntax_tree import StBranch
from .syntax_lexer import SyntaxLexer
from .syntax_parser import SyntaxParser
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail
from .command import Command


# typedefs
_T = TypeVar('_T')
CommandCallbackDecorator = Callable[[Callable[..., _T]], Command]


class CommandDispatchError(Exception):
    '''Raised by the dispatcher when something goes wrong'''

class UnknownCommandError(CommandDispatchError):
    '''Raised by the dispatcher when an unknown command is called'''


class CommandDispatcher:
    def __init__(self, **kwargs):
        self._commands = []  # type: List[Command]
        self.syntax_parser = kwargs['syntax_parser'] if 'syntax_parser' in kwargs else SyntaxParser()
        self.syntax_lexer  = kwargs['syntax_lexer'] if 'syntax_lexer' in kwargs else SyntaxLexer()

    def register(self, command: Command) -> None:
        self._commands.append(command)

    def command(self, syntax: str, **kwargs) -> CommandCallbackDecorator: 
        st_root = self.syntax_parser.parse(self.syntax_lexer.tokenize(syntax))

        def decorator(f: Callable[..., _T]) -> Command:
            cmd = Command(st_root, f, **kwargs)
            self.register(cmd)
            return cmd
            
        return decorator

    def dispatch(self, call: str, **callback_args) -> Any:
        max_score = 0
        best_fail = None

        for command in self._commands:
            match = CallMatch()
            try:
                return command.execute(call, match, callback_args)
            except CallMatchFail as fail:
                if match.score > max_score:
                    max_score = match.score
                    best_fail = fail
            
        if best_fail is not None:
            raise best_fail

        raise UnknownCommandError('Unknown command')

    def get_usage_lines(self) -> Iterable[str]:
        return chain.from_iterable(command.get_usage_lines() for command in self._commands)
