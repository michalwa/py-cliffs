import sys
from datetime import datetime
from clifford import *

clifford = CommandDispatcher()


# The decorator registers the function as the callback for the specified command
@clifford.command('set [loud] alarm at <time: int> (am|pm) [with message <message>]')
def command_set_alarm(match: CallMatch):

    # The callback recieves a `match` object describing the configuration
    # of the command matched by the call. The object has the following properties:
    # 
    #   match.tokens      - the full tokenized call
    #   match[param_name] - value of the specified parameter
    #   match.opt(i)      - boolean indicating whether the i-th optional sequence is present
    #   match.var(i)      - 0-based index of the present variant of the i-th variant group
    #

    loud = match.opt(0)                 # Check whether optional sequence is present
    time = match['time']                # Retrieve parameter values
    message = match['message']
    am_pm = ['am', 'pm'][match.var(0)]  # Get variant index

    # Print something out
    t = 'Setting ' + ('a loud ' if loud else 'an ') + f'alarm at {time} {am_pm.upper()}'
    if message is not None:
        t += f' with message: "{message}"'
    print(t)


# The user will have to use an escape sequence to type the single quote
@clifford.command("i [don't] like bread")
def command_like_bread(match: CallMatch):
    if not match.opt(0):
        print('I like bread too')
    else:
        print("I don't like bread either")


# Command callbacks can return values which will be passed to the caller of `dispatch()`
@clifford.command('eval <expr>')
def command_eval(match: CallMatch):
    return eval(match['expr'])


# Commands callbacks can recieve arguments from the caller of `dispatch()`
@clifford.command('tell time')
def command_tell_time(datetime: datetime):
    print(f"The time is {datetime}")


# All callback parameters are optional and indicate what the callback needs to recieve
@clifford.command('help', call_matcher=CallMatcher(case_sensitive=False))
def command_show_help():
    print('Known commands')
    print('--------------')

    # Use `get_usage_lines()` to automatically build a usage help message
    # `Command` objects can override their help messages
    print('\n'.join(clifford.get_usage_lines()))


if __name__ == '__main__':
    try:
        while True:
            try:

                # Callback args will be passed to command callbacks for successful command matches
                args = {'datetime': datetime.now()}

                result = clifford.dispatch(input('> '), **args)
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
