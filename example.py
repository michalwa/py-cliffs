import sys
import logging
from typing import Optional, Iterable
from datetime import datetime
from time import struct_time, strptime, strftime

from cliffs import *


# Set up logging
logger = logging.getLogger('cliffs.syntax_parser')
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

logger.addHandler(sh)


cli = CommandDispatcher()

# You can use custom call matchers to define custom parameter types.
custom_matcher = CallMatcher()
custom_matcher.register_type(lambda s: strptime(s, '%I:%M'), '12h_time')


# The decorator registers the function as the callback for the specified command
@cli.command('set [loud] alarm at <time:12h_time> (am|pm) [with message <message...*>]', matcher=custom_matcher)
def command_set_alarm(match: CallMatch):

    # The callback recieves a `match` object describing the configuration
    # of the command matched by the call. The object has the following properties:
    #
    #   match.tokens      - the full tokenized call
    #   match[param_name] - value of the specified parameter
    #   match.opt(i)      - boolean indicating whether the i-th optional sequence is present
    #   match.var(i)      - 0-based index of the present variant of the i-th variant group
    #

    # Check whether optional sequence is present
    loud = match.opts[0]  # type: bool
    # Retrieve parameter values
    time = match.params['time']  # type: struct_time
    message = match.params['message'] if match.opts[1] else None  # type: Optional[str]
    # Get variant index
    am_pm = ['am', 'pm'][match.vars[0]]  # type: str

    # Print something out
    t = 'Setting ' + ('a loud ' if loud else 'an ') + 'alarm at ' + strftime('%I:%M', time) + ' ' + am_pm.upper()
    if message is not None:
        t += f' with message: "{message}"'
    print(t)


# Tail parameters (`...`) collect all remaining tokens from the command call.
# Nothing can follow such parameters, anything after it will cause a `SyntaxError`.
#
# You can pass parameters directly as arguments to a callback.
@cli.command('(eval | =) <expr...*>', description='Evaluates a given expression.')
def command_eval(expr: str):

    # Command callbacks can return values which will be passed to the caller of `dispatch()`
    return eval(expr)


# You can use a colon `:` to assign identifiers to optional sequences and variant groups,
# these will be then added to parameters and can be recieved with an argument.
# Note that if you assign an identifier to a group, its state won't be present in the
# index-based array (`opts` or `vars`).
# These identifiers will not be displayed in the usage help.
@cli.command("i [don't]:negation like (bread|cheese):food")
def command_like_bread(negation: bool, food: int):
    food_name = ['bread', 'cheese'][food]
    if not negation:
        print(f'I like {food_name} too')
    else:
        print(f"I don't like {food_name} either")


# Command callbacks can also recieve additional arguments from the caller of `dispatch()`
@cli.command('tell time', description='Tells the date and time')
def command_tell_time(now: datetime):
    print(f"The time is {now}")


# You can assign custom classes to specific commands
class HiddenCommand(Command):
    def __init__(self, stx, callback, **kwargs):
        super().__init__(stx, callback, **kwargs)

    def get_usage_lines(self, **kwargs) -> Iterable[str]:
        return []


# Commands don't have to start with a literal.
#
# Keep in mind though that when matching fails, the most likely command will be guessed
# based on the beginning portion of the match.
#
# For example, when calling: `6 alarm at`, even though more tokens match the
# "set alarm at ..." command, the command below will be reported as missing arguments.
@cli.command('<n:int> times say <what>', command_class=HiddenCommand)
def command_repeat(n: int, what: str):
    for _ in range(n):
        print(what)


# There will be an info message logged that this command can be simplified
@cli.command('(exit|quit)')
def command_exit():
    print("Bye!")
    exit(0)


# All callback parameters are optional and indicate what the callback needs to recieve
@cli.command('help', matcher=CallMatcher(case_sensitive=False), description='Displays this help message')
def command_help():
    print('Known commands')
    print('--------------')

    # Use `get_usage_lines()` to automatically build a usage help message
    # `Command` objects can override their help messages
    print('\n'.join(cli.get_usage_lines(separator='')))


if __name__ == '__main__':
    try:
        while True:
            try:

                # Callback args will be passed to command callbacks for successful command matches
                args = {'now': datetime.now()}

                result = cli.dispatch(input('> '), **args)
                if result is not None:
                    print(f'= {result}')

            # `CallMatchFail` is raised when no command fully matched the call
            # (the error from the best matched command is returned)
            except CallMatchFail as fail:
                print(f'Invalid syntax: {fail}')

            # `UnknownCommandError` is raised when no command got a match score higher than 0
            # (no element was matched in any of the registered commands)
            except UnknownCommandError:
                print('Unknown command')

    except KeyboardInterrupt:
        pass
