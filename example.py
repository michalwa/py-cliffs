import sys
from clifford import Clifford, CallMatch, CallMatchFail

clifford = Clifford()

@clifford.command('set [loud] alarm at <time> (am|pm) [with message <message>]')
def set_alarm(match: CallMatch):
    loud = match.opt(0)
    time = match['time']
    am_pm = ['am', 'pm'][match.var(0)]
    message = match['message']

    t = 'Setting ' + ('a loud ' if loud else 'an ') + f'alarm at {time} {am_pm.upper()}'
    if message is not None:
        t += f' with message: "{message}"'
    
    print(t)

if __name__ == '__main__':
    try:
        while True:
            try:
                if not clifford.dispatch(input('> ')):
                    print('Unknown command')
            except CallMatchFail:
                print('Invalid syntax')
    except KeyboardInterrupt:
        pass
