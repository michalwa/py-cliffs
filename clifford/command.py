from typing import Tuple, Callable, Iterable
from .syntax_tree import StBranch
from .call_lexer import CallLexer
from .call_match import CallMatcher, CallMatch, CallMatchFail


# typedef
CommandCallback = Callable[[CallMatch], object]


class Command:
    def __init__(self, syntax: StBranch, callback: CommandCallback, **kwargs):
        self.syntax = syntax
        self.callback = callback
        self.call_lexer = kwargs['call_lexer'] if 'call_lexer' in kwargs else CallLexer()
        self.call_matcher = kwargs['call_matcher'] if 'call_matcher' in kwargs else CallMatcher()

    def execute(self, call: str, match: CallMatch) -> object:
        match.tokens = list(self.call_lexer.tokenize(call))

        left = self.syntax.match_call(match.tokens, self.call_matcher, match)
        if len(left) > 0:
            raise CallMatchFail('Too many arguments')

        return self.callback(match)

    def get_usage_lines(self) -> Iterable[str]:
        yield str(self.syntax)
