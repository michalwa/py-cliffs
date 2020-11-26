import inspect
from typing import Any, Callable, Iterable, Optional
from .utils import instance_or_kwargs, best
from .call_match import CallMatch, CallMatchFail
from .command import Command
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
          * parser: `SyntaxParser` or `dict` - The syntax parser to use to parse the syntax for new commands.
          * call_lexer: `CallLexer` or `dict` - The lexer to pass to new commands for tokenizing calls.
          * matcher: `CallMatcher` or `dict` - The matcher to pass to new commands for matching calls.
          * command_class: `type[Command]` - The class to construct for new commands.
        """

        self.parser = instance_or_kwargs(kwargs.get('parser', {}), SyntaxParser)
        self.command_class: type[Command] = kwargs.get('command_class', Command)

        self._commands: list[Command] = []

        # Kwargs to be passed to commands constructed with @command
        self._command_kwargs = {}
        if 'call_lexer' in kwargs:
            self._command_kwargs['lexer'] = kwargs['call_lexer']
        if 'matcher' in kwargs:
            self._command_kwargs['matcher'] = kwargs['matcher']

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
          * command_class: `Type[Command]` - The class to instantiate for this command
            (overrides the command class this dispatcher was initialized with).

        Refer to `Command.__init__` for additional keyword arguments.

        Returns
        -------
          * `Command`: The constructed, registered command.
        """

        parser = instance_or_kwargs(kwargs.get('parser', self.parser), SyntaxParser)

        syntax_root = parser.parse(syntax)
        command_class: type[Command] = kwargs.pop('command_class', self.command_class)

        def decorator(f: Callable) -> Command:
            # Read docstring if 'description' parameter is not given
            if 'description' not in kwargs and f.__doc__ is not None:
                # Dedent and remove leading and trailing empty lines
                kwargs['description'] = inspect.cleandoc(f.__doc__).strip('\n')

            cmd = command_class(syntax_root, f, **self._command_kwargs | kwargs)
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
          * Whatever the callback of the matched command returns.

        Raises
        ------
          * `CallMatchFail` of the best-matched command when no command fully
            matches the call.
          * `UnknownCommandError` when no appropriate command can be determined
            based on the tokens of the call.
        """

        matches: list[tuple[CallMatch, Command]] = []
        fails: list[tuple[CallMatchFail, float]] = []

        # Collect matches and fails from commands
        for command in self._commands:
            match = command.begin_match(call)

            try:
                command.match(match)
                matches.append((match, command))

            except CallMatchFail as fail:
                if match.score > 0:
                    fails.append((fail, match.score))

        # Find the match with the highest score and execute it
        if matches != []:
            best_match, matched_command = best(matches, lambda m: m[0].score)
            return matched_command.execute(best_match, callback_args)

        # If no command successfully matched, raise best scoring fail
        elif fails != []:
            best_fail, _ = best(fails, lambda f: f[1])
            raise best_fail

        # ...or unknown command if there are no fails scoring above 0
        else:
            raise UnknownCommandError('Unknown command')

    def get_usage(self, separator: Optional[str] = None, **kwargs) -> Iterable[str]:
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
            command_usage = list(command.get_usage(**kwargs))

            if command_usage != []:
                if separator is not None and i > 0:
                    lines.append(separator)

                lines += command_usage

        return lines
