from typing import Optional, Callable, Iterable
from inspect import signature
from .syntax_tree import StNode
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail
import textwrap


class Command:
    """Matches command calls against its syntax and controls callback dispatch."""

    def __init__(self, syntax: StNode, callback: Callable, **kwargs):
        """Initializes a command.

        Parameters
        ----------
          * syntax: `StNode` - The root of the syntax tree for this command.
          * callback: `(...) -> *` - The callback.
        """

        self.syntax = syntax
        self.callback = callback
        self.lexer = kwargs['lexer'] if 'lexer' in kwargs else CallLexer()
        self.matcher = kwargs['matcher'] if 'matcher' in kwargs else CallMatcher()
        self.description = kwargs.get('description', None)  # type: Optional[str]

    def match(self, call: str, match: CallMatch):
        """Tries to match the given call to this command's syntax and populates
        the given match instance.

        Parameters
        ----------
          * call: `str` - The call to match.
          * match: `CallMatch` - The match to populate.

        Raises
        ------
          * `CallMatchFail` when matching fails or the command tokens are not fully
            exhausted at the end of the match.
        """

        match.tokens = list(self.lexer.tokenize(call))

        left = self.syntax.match_call(match.tokens, self.matcher, match)
        if len(left) > 0:
            raise CallMatchFail('Too many arguments')

    def execute(self, match: CallMatch, callback_args={}) -> object:
        """Executes the command callback with the given match. By default,
        the match must be the result of calling the `match()` method of this object.

        Parameters
        ----------
          * match: `CallMatch` - The match to dispatch to the callback.
          * callback_args: `dict` (optional) - Additional arguments to pass to the callback.
            Defaults to none.

        Returns
        -------
          * `*`: Whatever is returned by the callback.
        """

        # Pass only those args that are required by the callback signature
        sig = signature(self.callback)
        callback_args.update({'match': match})
        callback_args.update(match.params)
        args = dict((p, callback_args[p]) for p in sig.parameters if p in callback_args)

        return self.callback(**args)

    def get_usage_lines(self, **kwargs) -> Iterable[str]:
        """Returns the auto-generated usage help message for this command.

        Keyword arguments
        -----------------
          * max_width: `int` - The width to wrap the usage help message to (0 for no wrapping).
          * indent_width: `int` - The width of the indent for the command description.

        Returns
        -------
          * `Iterable[str]`: The lines of the usage help message.
        """

        max_width = kwargs.get('max_width', 70)
        indent_width = kwargs.get('indent_width', 4)

        if max_width != 0:
            for line in textwrap.wrap(str(self.syntax), width=max_width):
                yield line
        else:
            yield str(self.syntax)

        if self.description is not None:
            if max_width != 0:
                wrap_options = {
                    'width': max_width,
                    'initial_indent': ' ' * indent_width,
                    'subsequent_indent': ' ' * indent_width
                }

                for line in textwrap.wrap(self.description, **wrap_options):
                    yield line
            else:
                yield self.description
