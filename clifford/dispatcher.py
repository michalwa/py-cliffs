from typing import Type, TypeVar, Optional, Dict, List, Iterable, Tuple, Callable, Any
from .syntax_tree import StBranch
from .syntax_lexer import SyntaxLexer
from .syntax_parser import SyntaxParser
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail
from .command import Command


# typedefs
_T = TypeVar('_T')


class CommandDispatchError(Exception):
    '''Raised by the dispatcher when something goes wrong'''

class UnknownCommandError(CommandDispatchError):
    '''Raised by the dispatcher when an unknown command is called'''


class CommandDispatcher:
    def __init__(self, **kwargs):
        self._commands = []  # type: List[Command]
        self.syntax_parser = kwargs['syntax_parser'] if 'syntax_parser' in kwargs else SyntaxParser()
        self.syntax_lexer = kwargs['syntax_lexer'] if 'syntax_lexer' in kwargs else SyntaxLexer()

    def register(self, command: Command) -> None:
        self._commands.append(command)

    def command(self, syntax: str, **kwargs) -> Callable[[Callable[..., _T]], Command]:
        st_root = self.syntax_parser.parse(self.syntax_lexer.tokenize(syntax))
        command_class = kwargs['command_class'] if 'command_class' in kwargs else Command  # type: Type[Command]

        def decorator(f: Callable[..., _T]) -> Command:
            cmd = command_class(st_root, f, **kwargs)
            self.register(cmd)
            return cmd
            
        return decorator

    def dispatch(self, call: str, **callback_args) -> Any:
        best_succ_match = None  # Highest-scoring successful match
        best_command = None     # Command having the highest-scoring successful match
        best_fail_match = None  # Highest-scoring failed match
        best_fail = None        # Exception from the highest-scoring failed match

        # Match all commands and look for the one with the highest score
        for command in self._commands:
            match = CallMatch()

            try:
                command.match(call, match)

                if best_succ_match is None or match.score > best_succ_match.score:
                    best_succ_match = match
                    best_command = command

            except CallMatchFail as fail:
                temp_fail = fail
                
                if best_fail_match is None or match.score > best_fail_match.score:
                    best_fail_match = match
                    best_fail = fail

        # If the highest-scoring match was successful, execute the command
        if best_command is not None:
            return best_command.execute(best_succ_match, callback_args)

        # Otherwise raise the error from the highest-scoring match
        elif best_fail_match.score > 0:
            raise best_fail

        # Or unknown command error if it's 0
        else:
            raise UnknownCommandError('Unknown command')

    def get_usage_lines(self, separator: Optional[str] = None, **kwargs) -> Iterable[str]:
        lines = []

        for command in self._commands:
            command_lines = list(command.get_usage_lines(**kwargs))

            if command_lines != []:
                lines += command_lines

                if separator is not None:
                    lines.append(separator)

        lines = lines[:-1]
        return lines
