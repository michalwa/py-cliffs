from typing import Optional, Callable, Iterable
from inspect import signature
from .utils import instance_or_kwargs
from .syntax_tree import Node as SyntaxNode
from .call_lexer import CallLexer
from .call_match import CallMatch, CallMatchFail
from .call_matcher import CallMatcher
import textwrap


class Command:
    """Matches command calls against its syntax and controls callback dispatch."""

    def __init__(self, syntax: SyntaxNode, callback: Callable, **kwargs):
        """Initializes a command.

        Parameters
        ----------
          * syntax: `StNode` - The root of the syntax tree for this command.
          * callback: `(...) -> *` - The callback.

        Keyword arguments
        -----------------
          * lexer: `CallLexer` - The lexer to use to tokenize incoming calls.
          * matcher: `CallMatcher` - The matcher to use to match calls against the syntax of this command.
          * description: `str` - The description to include in the usage help message. Ignored if hidden is True.
          * hidden: `bool` - Whether the usage help message should exclude this command entirely.
        """

        self.syntax = syntax
        self.callback = callback
        self.lexer = instance_or_kwargs(kwargs.get('lexer', {}), CallLexer)
        self.matcher = instance_or_kwargs(kwargs.get('matcher', {}), CallMatcher)
        self.description = kwargs.get('description', None)  # type: Optional[str]
        self.hidden = kwargs.get('hidden', False)  # type: bool

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

        left = self.syntax.match(match.tokens, self.matcher, match)
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
          * Whatever is returned by the callback.
        """

        # Pass only those args that are required by the callback signature
        sig = signature(self.callback)
        callback_args.update({'match': match})
        callback_args.update(match._params)
        args = dict((p, callback_args[p]) for p in sig.parameters if p in callback_args)

        return self.callback(**args)

    def get_usage(self, **kwargs) -> Iterable[str]:
        """Returns the auto-generated usage help message for this command.

        Keyword arguments
        -----------------
          * max_width: `int` - The width to wrap the usage help message to (0 for no wrapping).
          * indent_width: `int` - The width of the indent for the command description.

        Returns
        -------
          * `Iterable[str]`: The lines of the usage help message.
        """

        if self.hidden:
            return []

        max_width = kwargs.get('max_width', 100)
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
                    'subsequent_indent': ' ' * indent_width,
                    'expand_tabs': True,
                }

                for desc_line in self.description.splitlines():
                    if desc_line == '':
                        yield desc_line
                    else:
                        for line in textwrap.wrap(desc_line, **wrap_options):
                            yield line
            else:
                for desc_line in self.description.splitlines():
                    yield desc_line
