from typing import Optional, Tuple, Callable, Iterable, Any
from inspect import signature
from .syntax_tree import StBranch
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail
import textwrap


class Command:
    def __init__(self, syntax: StBranch, callback: Callable[..., Any], **kwargs):
        self.syntax = syntax
        self.callback = callback
        self.lexer = kwargs['lexer'] if 'lexer' in kwargs else CallLexer()
        self.matcher = kwargs['matcher'] if 'matcher' in kwargs else CallMatcher()
        self.description = kwargs.get('description', None)  # type: Optional[str]

    def match(self, call: str, match: CallMatch):
        match.tokens = list(self.lexer.tokenize(call))

        left = self.syntax.match_call(match.tokens, self.matcher, match)
        if len(left) > 0:
            raise CallMatchFail('Too many arguments')

    def execute(self, match: CallMatch, callback_args = {}) -> object:

        # Pass only those args that are required by the callback signature
        sig = signature(self.callback)
        callback_args.update({'match': match})
        callback_args.update(match.params)
        args = dict((p, callback_args[p]) for p in sig.parameters if p in callback_args)

        return self.callback(**args)

    def get_usage_lines(self, **kwargs) -> Iterable[str]:
        max_width = kwargs.get('max_width', 70)
        indent_width = kwargs.get('indent_width', 4)

        for line in textwrap.wrap(str(self.syntax), width=max_width):
            yield line

        if self.description is not None:
            wrap_options = {
                'width': max_width,
                'initial_indent': ' ' * indent_width,
                'subsequent_indent': ' ' * indent_width
            }

            for line in textwrap.wrap(self.description, **wrap_options):
                yield line
