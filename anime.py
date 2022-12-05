from argparse import RawTextHelpFormatter, ArgumentParser
from utils import dir_path
from sessionManager import SessionManager
from main import mainTUI

def range_parser(string):
    if string == '': return {'start':0, 'end':0}

    slicestring = [*string.split(':'), ''][:2]
    return {'start':slicestring[0], 'end':slicestring[1]}

parser = ArgumentParser(description='plays anime from terminal', formatter_class=RawTextHelpFormatter)

parser.add_argument('name',          action='store', default='', type=str, nargs='*',
                    help='anime name')
parser.add_argument('-y','--yes',    action='store_true',
                    help='use all default options')
parser.add_argument('--episodes',    action='store', default={'start':0, 'end':0},    type=range_parser, metavar='RANGE',
                    help='range of episodes to watch\n         n    - same as n:-1\n         n:n  - range of episodes')
parser.add_argument('--player',      action='store', default='mpv', type=str,
                    help='player to run the anime\n         mpv  - use MPV player(default)\n         none - run as server\n         xxxx - use any other player, example: mplayer')
parser.add_argument('--update',      action='store_true',         
                    help='update the local list')
parser.add_argument('--synch',      action='store_true',         
                    help='update the local list synchronously')
parser.add_argument('--server',      action='store_true',         
                    help='serves a list of animes as a m3u playlist through the network. Use colons (,) to split each anime')
parser.add_argument('--config-dir',    action='store', default='',    type=dir_path, metavar='config directory',
                    help='directory for the watch list')

args = parser.parse_args()

# TODO -> implement on demand server TUI
# TODO -> implement configuration TUI
#   TODO -> config file
# TODO -> add english translation

# print(getTotalEpisodesCount('boku no hero Academia'))

if args.update:
    sessionmanager = SessionManager(root=args.config_dir)
    sessionmanager.dump()

    print('O total de episódios dos animes do histórico foram sincronizados')
else:
    mainTUI(args.name, args.player, args.episodes, args.config_dir, args.yes)
