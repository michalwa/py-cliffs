from typing import Tuple, Callable, Iterable, Any
from inspect import signature
from .syntax_tree import StBranch
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail


class Command:
    def __init__(self, syntax: StBranch, callback: Callable[..., Any], **kwargs):
        self.syntax = syntax
        self.callback = callback
        self.call_lexer = kwargs['call_lexer'] if 'call_lexer' in kwargs else CallLexer()
        self.call_matcher = kwargs['call_matcher'] if 'call_matcher' in kwargs else CallMatcher()

        self.usage_lines = [str(self.syntax)]

    def execute(self, call: str, match: CallMatch, callback_args = {}) -> object:
        match.tokens = list(self.call_lexer.tokenize(call))

        left = self.syntax.match_call(match.tokens, self.call_matcher, match)
        if len(left) > 0:
            raise CallMatchFail('Too many arguments')

        # Pass only args required by the callback signature
        sig = signature(self.callback)
        callback_args.update({'match': match})
        callback_args.update(match.params)
        args = dict((p, callback_args[p]) for p in sig.parameters if p in callback_args)

        return self.callback(**args)

    def get_usage_lines(self) -> Iterable[str]:
        return self.usage_lines
