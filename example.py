import sys
import logging
from typing import Optional
from datetime import datetime
from time import strptime, strftime
from cliffs import *


# Set up logging
logger = logging.getLogger('cliffs.syntax_parser')
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

logger.addHandler(sh)


# You can use custom call matchers to define custom parameter types.
custom_matcher = CallMatcher()
custom_matcher.register_type(lambda s: strptime(s, '%I:%M'), '12h_time')

cli = CommandDispatcher(matcher=custom_matcher)


# The decorator registers the function as the callback for the specified command
@cli.command('set [loud] alarm at <time:12h_time> (am|pm) [with message <message...>]')
def command_set_alarm(match: CallMatch):

    # The callback recieves a `match` object describing the configuration
    # of the command matched by the call. The object has the following properties:
    #
    #   match.tokens      - the full tokenized call
    #   match[param_name] - value of the specified parameter
    #   match.optional(i) - boolean indicating whether the i-th optional sequence is present
    #   match.variant(i)  - 0-based index of the present variant of the i-th variant group
    #

    # Check whether optional sequence is present
    loud = match.optional(0)
    # Retrieve parameter values
    time = match['time']
    message = match['message'] if match.optional(1) else None
    # Get variant index
    am_pm = ['am', 'pm'][match.variant(0)]

    # Print something out
    t = 'Setting ' + ('a loud ' if loud else 'an ') + 'alarm at ' + strftime('%I:%M', time) + ' ' + am_pm.upper()
    if message is not None:
        t += f' with message: "{message}"'
    print(t)


# You can pass parameters directly as arguments to a callback.
# This is actually the preferred way of setting up commands, the above example
# was just for demonstration purposes.
@cli.command('(eval | =) <expr...>')
def command_eval(expr: str):
    """Evaluates a given expression."""

    # Command callbacks can return values which will be passed to the caller of `dispatch()`
    return eval(expr)


# Most syntax elements support "greedy" matching with variant groups
# - the variant with the most matching elements will be chosen
@cli.command('scream|scream <what>')
def command_scream(match: CallMatch, what: Optional[str] = None):
    if match.variant(0) == 0:
        print("AAAAAAAAAAAAAAAAAAAAAAAA")
    else:
        print(f"{what.upper()}!")


# You can use a colon `:` to assign identifiers to optional sequences and variant groups,
# these will be then added to parameters and can be recieved with an argument.
# Note that if you assign an identifier to a group, its state won't be present in the
# index-based array (`opts` or `vars`).
# These identifiers will not be displayed in the usage help.
@cli.command("i [dont]:negation like (bread|cheese):food")
def command_like_bread(negation: bool, food: int):
    food_name = ['bread', 'cheese'][food]
    if not negation:
        print(f'I like {food_name} too')
    else:
        print(f"I don't like {food_name} either")


# Command callbacks can also recieve additional arguments from the caller of `dispatch()`
@cli.command('{tell time}')
def command_tell_time(now: datetime):
    """Tells date and time"""

    print(f"The time is {now}")


# Commands don't have to start with a literal.
# Keep in mind though that when matching fails, the most likely command will be guessed
# based on the beginning portion of the match.
# For example, when calling: `6 alarm at`, even though more tokens match the
# "set alarm at ..." command, the command below will be reported as missing arguments.
@cli.command('<n:int> times say <what>', hidden=True)
def command_repeat(n: int, what: str):
    for _ in range(n):
        print(what)


# There will be an info message logged that this command can be simplified
@cli.command('(exit|quit|(good bye)|leave)', parser={'all_case_insensitive': True})
def command_exit():
    print("Bye!")
    exit(0)


# Literals have priority over parameters
@cli.command('foo <bar>|foo bar')
def command_foo(bar = None):
    print(bar)


# "help" will be matched case-insensitively
@cli.command('help^')
def command_help():
    """Displays this help message"""

    print('Known commands')
    print('--------------')

    # Use `get_usage()` to automatically build a usage help message
    # `Command` objects can override their help messages
    print('\n'.join(cli.get_usage(separator='')))


if __name__ == '__main__':
    try:
        while True:
            try:

                # Callback args will be passed to command callbacks for successful command matches
                args = {'now': datetime.now()}

                command = input('\033[94m> ')
                print('\033[0m', end='')

                result = cli.dispatch(command, **args)
                if result is not None:
                    print(f'= {result}')

            # `CallMatchFail` is raised when no command fully matched the call
            # (the error from the best matched command is returned)
            except CallMatchFail as fail:
                print(f'\033[91mInvalid syntax: {fail}\033[0m')

            # `UnknownCommandError` is raised when no command got a match score higher than 0
            # (no element was matched in any of the registered commands)
            except UnknownCommandError:
                print('\033[91mUnknown command\033[0m')

    except KeyboardInterrupt:
        pass
