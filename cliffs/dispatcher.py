from typing import Any, Callable, Iterable, List, Optional, Type

from .call_match import CallMatch, CallMatchFail
from .command import Command
from .syntax_lexer import SyntaxLexer
from .syntax_parser import SyntaxParser


class CommandDispatchError(Exception):
    """Raised by the dispatcher when something goes wrong"""


class UnknownCommandError(CommandDispatchError):
    """Raised by the dispatcher when an unknown command is called"""


class CommandDispatcher:
    """Manages registered commands, allows registering new commands.
    Controls the dispatch of command calls.
    """

    def __init__(self, **kwargs):
        """Initializes a dispatcher.

        Keyword arguments
        -----------------
          * syntax_parser: `SyntaxParser` - The syntax parser to use to parse new commands.
          * syntax_lexer: `SyntaxLexer` - The lexer to use to
        """

        self._commands = []  # type: List[Command]
        self.syntax_parser = kwargs['syntax_parser'] if 'syntax_parser' in kwargs else SyntaxParser()
        self.syntax_lexer = kwargs['syntax_lexer'] if 'syntax_lexer' in kwargs else SyntaxLexer()

    def register(self, command: Command) -> None:
        """Registers the given command.

        Parameters
        ----------
          * command: `Command` - The command to register.
        """
        self._commands.append(command)

    def command(self, syntax: str, **kwargs) -> Callable[[Callable], Command]:
        """(decorator)
        Registers a command with the specified syntax and the annotated function
        as the callback.

        Parameters
        ----------
          * syntax: `str` - The syntax for the command.

        Keyword arguments
        -----------------
          * command_class: `Type[Command]` - The class to instantiate for this command.

        Returns
        -------
          * `Command`: The constructed, registered command.
        """

        st_root = self.syntax_parser.parse(self.syntax_lexer.tokenize(syntax))
        command_class = kwargs['command_class'] if 'command_class' in kwargs else Command  # type: Type[Command]

        def decorator(f: Callable) -> Command:
            cmd = command_class(st_root, f, **kwargs)
            self.register(cmd)
            return cmd

        return decorator

    def dispatch(self, call: str, **callback_args) -> Any:
        """Tries to dispatch the given command calls to the appropriate command.

        All keyword arguments will be passed as additional arguments to the
        appropriate callback.

        Parameters
        ----------
          * call: `str` - The call to process and dispatch.

        Returns
        -------
          * `*`: Whatever the callback of the matched command returns.

        Raises
        ------
          * `CallMatchFail` of the best-matched command when no command fully
            matches the call.
          * `UnknownCommandError` when no appropriate command can be determined
            based on the tokens of the call.
        """

        best_succ_match = None  # Highest-scoring successful match
        best_command = None     # Command having the highest-scoring successful match
        best_fail_match = None  # Highest-scoring failed match
        best_fail = None        # Exception from the highest-scoring failed match

        # Match all commands and look for the one with the highest score
        for command in self._commands:
            match = CallMatch(call)

            try:
                command.match(call, match)

                if best_succ_match is None or match.score > best_succ_match.score:
                    best_succ_match = match
                    best_command = command

            except CallMatchFail as fail:
                if best_fail_match is None or match.score > best_fail_match.score:
                    best_fail_match = match
                    best_fail = fail

        # If the highest-scoring match was successful, execute the command
        if best_succ_match is not None and best_command is not None:
            return best_command.execute(best_succ_match, callback_args)

        # Otherwise raise the error from the highest-scoring match
        elif best_fail_match is not None and best_fail_match.score > 0 and best_fail is not None:
            raise best_fail

        # Or unknown command error if it's 0
        else:
            raise UnknownCommandError('Unknown command')

    def get_usage_lines(self, separator: Optional[str] = None, **kwargs) -> Iterable[str]:
        """Returns the message composed of usage help messages of registered commands
        as individual lines.

        Parameters
        ----------
          * separator: `str` (optional) - The separator to use to separate blocks
            of lines returned by individual commands. Defaults to None.

        Keyword arguments
        -----------------
          * max_width: `int` - The width to wrap the usage help message to (0 for no wrapping).
          * indent_width: `int` - The width of the indent for the command description.

        Returns
        -------
          * `Iterable[str]`: The individual lines of the usage help message.
        """

        lines = []

        for i, command in enumerate(self._commands):
            command_lines = list(command.get_usage_lines(**kwargs))

            if command_lines != []:
                if separator is not None and i > 0:
                    lines.append(separator)

                lines += command_lines

        return lines
