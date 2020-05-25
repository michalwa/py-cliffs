import sys
from clifford import *

clifford = CommandDispatcher()


@clifford.command('set [loud] alarm at <time: int> (am|pm) [with message <message>]')
def command_set_alarm(match: CallMatch):
    loud = match.opt(0)
    time = match['time']
    am_pm = ['am', 'pm'][match.var(0)]
    message = match['message']

    t = 'Setting ' + ('a loud ' if loud else 'an ') + f'alarm at {time} {am_pm.upper()}'
    if message is not None:
        t += f' with message: "{message}"'
    
    print(t)


@clifford.command('i [don\'t] like bread')
def command_like_bread(match: CallMatch):
    if not match.opt(0):
        print('I like bread too')
    else:
        print("I don't like bread either")


@clifford.command('help', call_matcher=CallMatcher(case_sensitive=False))
def command_show_help(match: CallMatch):
    print('Known commands')
    print('--------------')
    print('\n'.join(clifford.get_usage_lines()))


@clifford.command('exit')
def command_exit(match: CallMatch):
    print('Bye!')
    exit(0)


if __name__ == '__main__':
    try:
        while True:
            try:
                clifford.dispatch(input('> '))
            except CallMatchFail as fail:
                print(f'Invalid syntax: {fail}')
            except UnknownCommandError:
                print('Unknown command')
    except KeyboardInterrupt:
        pass
