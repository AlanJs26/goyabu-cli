from argparse import RawTextHelpFormatter, ArgumentParser
from os import path,makedirs

import json

from .anilistManager import AnilistManager, MissingToken, MissingUsername
from .sessionManager import SessionManager
from .scraperManager import SCRAPERS
from .cli import mainTUI, configTUI, Config, serverTUI
from .translation import t, warning

def preferedScraperParser(string:str):
    if string == '': return []

    return string.split(',')

def range_parser(string:str):
    if string == '': return {'start':0, 'end':0}

    if ':' not in string:
        return {'start':int(string)-1, 'end':int(string)}
    slicestring = [int(x) for x in [*string.split(':'), ''][:2]]
    return {'start':slicestring[0]-1, 'end':slicestring[1]-1}

def dir_path(string):
    if string == '': return ''
    new_string = path.expanduser(string)

    if string == '~/.goyabucli':
        makedirs(new_string, exist_ok=True)

    if path.isdir(new_string):
        return new_string
    else:
        print(f"'{string}' is not a path to a directory")
        print(f"do you want to create it?")
        choice = str(input('[y/N]: '))

        if choice.lower() == 'y':
            makedirs(new_string, exist_ok=True)
            return new_string

        print("Exiting")
        exit()



parser = ArgumentParser(description='plays anime from terminal', formatter_class=RawTextHelpFormatter)

parser.add_argument('name',          action='store', default='', type=str, nargs='*',
                    help='anime name')
parser.add_argument('-y','--yes',    action='store_true',
                    help='accept all default options')
parser.add_argument('--episodes',    action='store', default={'start':0, 'end':0},    type=range_parser, metavar='RANGE',
                    help='range of episodes to watch. Ex: an range of 1:5 will play all the episodes from one to five')
parser.add_argument('--player',      action='store', default='mpv', type=str,
                    help='player to run the anime\n         mpv  - use MPV player(default)\n         xxxx - use any other player, example: mplayer')
parser.add_argument('--scraper',      action='store', default=[], type=preferedScraperParser,
                    help='give priority to given scraper when using --yes argument.')
parser.add_argument('--update',      action='store_true',         
                    help='fetch the latest information for the animes in history')
parser.add_argument('--server',      action='store_true',         
                    help='serves a list of animes as a m3u playlist through the network.')
parser.add_argument('--anilist_sync', '--sync',      choices=['prefer_local', 'prefer_remote', 'replace_local', 'replace_remote'],         
                    help='sync with anilist\n    --prefer_local      fetch the anilist watchlist but prefer the local list on conflict\n    --prefer_remote     fetch the anilist watchlist but prefer the remote list on conflict\n    --replace_local     replace the local list with the remote\n    --replace_remote    replace the remote list with the local')
parser.add_argument('--config',      action='store_true',         
                    help='change config')
parser.add_argument('--config-dir',    action='store', default='~/.goyabucli',    type=dir_path, metavar='config directory',
                    help='directory for the watch list')

args = parser.parse_args()

# DONE -> implement on demand server TUI
# TODO -> add 'planning to watch' animes in main list as a filter
# DONE -> implement scraper filter to anime selection
# DONE -> implement configuration TUI
#   DONE -> config file
# DONE -> anilist integration
# TODO -> finish translation

def main():

    config = Config(config_dir=args.config_dir, player=args.player, anilist_username='', token='', silent=False)

    if path.isfile(path.join(args.config_dir, 'config.json')):
        with open(path.join(args.config_dir, 'config.json')) as file:
            content = json.load(file)

            if 'anilist_username' in content:
                config.anilist_username = content['anilist_username']
            if 'token' in content:
                config.token = content['token']
            if 'config_dir' in content and args.config_dir == parser.get_default('config_dir'):
                config.config_dir = content['config_dir']
            if 'player' in content and args.player == parser.get_default('player'):
                config.player = content['player']
            if 'silent' in content:
                config.silent = content['silent']
                
    anilistManager = AnilistManager(config.anilist_username, config.token, scrapers=SCRAPERS, silent=config.silent)

    if args.update:
        print(t('Atualizando o histórico...'))
        sessionmanager = SessionManager(root=args.config_dir, scrapers=SCRAPERS)
        history_size = len(sessionmanager.session_items)

        anilistManager.update_session(sessionmanager, True)
        sessionmanager.dump(verbose=True, number_to_update=history_size)

        print(t('O total de episódios dos animes do histórico foram sincronizados'))
    elif args.config:
        configTUI(config, anilistManager)
    elif args.anilist_sync:
        sessionmanager = SessionManager(root=args.config_dir, scrapers=SCRAPERS)

        try: 
            if args.anilist_sync == 'prefer_local':
                anilistManager.merge_session(sessionmanager)
            elif args.anilist_sync == 'prefer_remote':
                anilistManager.merge_session(sessionmanager, preferRemote=True)
            elif args.anilist_sync == 'replace_local':
                sessionmanager.session_items = []

                sessionmanager.add_session_items(anilistManager.get_watching())
            elif args.anilist_sync == 'replace_remote':
                anilistManager.set_watching(sessionmanager.session_items)

            sessionmanager.dump(verbose=True)
        except MissingToken:
            if not config.silent:
                warning("wasn't possible sync with anilist. Missing authentification token")
                warning("to get rid of this message, mark the option 'silent' to True in the config")
                warning("    eg: anime --config")
                exit()
        except MissingUsername:
            if not config.silent:
                warning("wasn't possible sync with anilist. Missing username")
                warning("to get rid of this message, mark the option 'silent' to True in the config")
                warning("    eg: anime --config")
                exit()

        print(t('Sincronização Completa'))

    elif args.server:
        serverTUI(anilistManager, ' '.join(args.name), args.episodes, args.yes, args.scraper, config=config)
    else:
        mainTUI(anilistManager, ' '.join(args.name), args.episodes, args.yes, args.scraper, config=config)

if __name__ == "__main__":
    main()
