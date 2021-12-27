import os, errno
from datetime import datetime
import json
import termtables as tt
from dropdown import interactiveTable, bcolors, isWindows
from time import sleep
from argparse import RawTextHelpFormatter, ArgumentParser
from copy import deepcopy
from rawserver import serveRawText
from scrappers.utils import runInParallel 
from shutil import which

def dir_path(string):
    if string == '': return ''
    new_string = os.path.expanduser(string)
    if os.path.isdir(new_string):
        return new_string
    else:
        raise NotADirectoryError(string)

parser = ArgumentParser(description='plays anime from terminal', formatter_class=RawTextHelpFormatter)

parser.add_argument('name',          action='store', default='',    type=str, nargs='?',
                    help='anime name')
parser.add_argument('-s','--silent', action='store_true',
                    help='minimal output')
parser.add_argument('-y','--yes',    action='store_true',
                    help='use all default options')
parser.add_argument('--episodes',    action='store', default='',    type=str, metavar='RANGE',
                    help='range of episodes to watch\n         n    - single episode\n         n:n  - range of episodes')
parser.add_argument('--player',      action='store', default='mpv', type=str,
    help='player to run the anime\n         mpv  - use MPV player(default)\n         none - run as server\n         xxxx - use any other player, example: mplayer')
parser.add_argument('--update',      action='store_true',         
                    help='update the local list')
parser.add_argument('--config-dir',    action='store', default='',    type=dir_path, metavar='config directory',
                    help='directory for the watch list')

args = parser.parse_args()

if args.update == True:
    args.player = 'none'
    args.episodes = ''
    args.silent = True


slicelist = ['', '']
chosenEngine = 'goyabu'

if args.episodes:
    slicelist = args.episodes.split(':')
    if len(slicelist) == 1: slicelist.append('')


# read last session file, if don't exist create one
lastSession={}
if args.config_dir != '':
    sessionpath = args.config_dir + ('/' if args.config_dir[-1] != '/' else '') + '.anime-lastsession.json'
else:
    sessionpath = os.path.join(os.path.dirname(__file__), '.anime-lastsession.json')
if os.path.isfile(sessionpath):
    with open(sessionpath) as rawjson:
        lastSession = json.load(rawjson)
else:
    with open(sessionpath, 'w') as rawjson:
        json.dump({}, rawjson)

def nameTrunc(text, length):
    columns = os.get_terminal_size().columns
    if columns < length:
        nameSlice = slice(None, len(text)-(length-columns))
        return text[nameSlice]+'...'
    return text

if len(lastSession) == 0 and args.update:
    print('the watch list if empty. Watch a episode first.')
    exit()

# Format last session table, highligthing completed animes
tableVals = []
for i,name in enumerate(lastSession):
    eps = lastSession[name]["numberOfEpisodes"]
    epsComputed = lastSession[name]["numberOfEpisodesComputed"]
    watchDate = lastSession[name]["date"]
    lastep = lastSession[name]["lastep"]
    if lastep == epsComputed and lastep < eps:
        tableVals.append(
[i+1, f'{bcolors["grey"]}{nameTrunc(name, 45+len(name))} - Episódio {lastep} [{epsComputed}/{eps}]{bcolors["end"]}', watchDate]
        )
    elif lastep < eps:
        tableVals.append(
[i+1, f'{nameTrunc(name, 45+len(name))} - Episódio {lastep} [{epsComputed}/{eps}]', watchDate]
        )
    else:
        tableVals.append(
[i+1, f'{bcolors["green"]}{nameTrunc(name, 40+len(name))} - Completo{bcolors["end"]}', watchDate]
#  [i+1, f'{bcolors["green"]}{nameTrunc(name, 45+len(name))} - Completo [{epsComputed}/{eps}]{bcolors["end"]}', watchDate]
        )




# Print the interactive Last Session table and remove the selected items
if len(lastSession) and args.name == '' and args.yes == False and args.update == False:
    results = [[],[],None]

    while len(results[1]) != 1 and results[0] != None:
        results = interactiveTable(tableVals[::-1], ["", "Sessões Anteriores", "Data"], "rcc", behaviour='multiSelectWithText', maxListSize=17, hintText='Nome do Anime[1]: ', highlightRange=(2,2))
        if results[0] == None: continue

        posToRemove = [len(tableVals)-1-item[0] for item in results[1][1:]]
        tableVals = [item for i, item in enumerate(tableVals) if i not in posToRemove]

    posToMaintain = [item[0] for item in tableVals]
    lastSession = {k: lastSession[k] for i,k in enumerate(lastSession) if i+1 in posToMaintain}

    if results[0] != None and len(results[1]) == 1 and results[-1] == '':
        args.name = str(results[0][0])
    else:
        args.name = results[-1]

#  If the search term is empty and exists last session items, choose the first last session
if args.name == '':
    if len(lastSession):
        args.name = '1'
    else:
        try:
            args.name = str(input('Nome do Anime: '))
        except KeyboardInterrupt:
            exit()

        if args.name == '':
            print('Insira um nome válido para continuar')
            exit()

from animeScrapper import animeInfo, searchAnime

#  If users choses one of last session items
if args.name.isdigit() and int(args.name) <= len(lastSession):
    args.name = list(lastSession.keys())[int(args.name)-1]
    args.yes = True
    chosenEngine = lastSession[args.name]['engine']
    if args.episodes == '':
        slicelist = [str(lastSession[args.name]['lastep']), '']

if args.update == False:
    rawnamelist = searchAnime(args.name, engines=['goyabu', 'vizer'])[0]
    namelist = []
    for engine in rawnamelist:
        for item in rawnamelist[engine]:
            namelist.append([item, engine])

else:
    namelist = []

if len(namelist) == 0 and args.update == False:
    print(f'\nNenhum anime com o nome "{args.name}" foi encontrado. Tente outro nome.')
    exit()

# print a interactive table to choose the anime
if  args.yes == False and args.update == False:
    
    tableValsOrig = [[i+1, namelist[i][0], namelist[i][1]] for i in range(len(namelist))]
    tableVals = [[i+1, nameTrunc(namelist[i][0], 15+len(namelist[i][0])), namelist[i][1]] for i in range(len(namelist))]
    result = interactiveTable(tableVals, ["", "Animes", "engine"], "rll", maxListSize=17, highlightRange=(2,2))
    args.name = tableValsOrig[result[0][0]-1][1]
    chosenEngine = result[0][-1]


if args.update == False:
    #  episodes = animeInfo('episodes', query=args.name)['goyabu', 'vizer']
    episodes = animeInfo('episodes', query=args.name, engines=[chosenEngine])[chosenEngine]
    episodesNames = [name for name,_ in episodes.items()]
    videolist = [link for _,link in episodes.items()]
else: 
    episodes = []
    episodesNames = []
    videolist = []

if not args.silent:
    table = tt.to_string(
        [[i+1, nameTrunc(episodesNames[i], len(episodesNames[i])+15)] for i in range(len(episodesNames))],
        header=["","Episódios"],
        style=tt.styles.rounded,
        alignment="rl",
    )
    table = table.split('\n')
    print('\n'.join(table[0:3]+table[1::2][1:]+table[-1:]))


if slicelist == ['']:
    if not args.silent:
        print('''
        n - único episódio
        n:n - intervalo de episódios
        todos - todos os episódios
        ''')
    try:
        slicelist = str(input('Episódios para assistir [todos]: ')).split(':') if not args.yes else ['todos']
        slicelist.append('')
    except KeyboardInterrupt:
        print('')
        os._exit(0)


# extract the choosen range from the fetched lists
count = 1
slicelist = [int(i) if i.isdigit() else None for i in slicelist]
if any(slicelist) and args.episodes and args.update == False:
    count = slicelist[0] or count

    videolist     =     videolist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]
    episodesNames = episodesNames[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]


# create the playlist file for the player
fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Ep {count} - {args.name}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{args.name}.m3u')

if not args.silent: print(f'Salvando em "{filepath}"')

# if the destiny folder dont exits, create it
if not os.path.exists(folderpath):
    try:
        os.makedirs(folderpath)
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

if args.update == False:
    with open(filepath, 'w') as writer:
        writer.writelines(fileText)

if args.update == False:
    newSessionItem = {
        #  'episodes': [[namelist[i], videolist[i]] for i in range(len(namelist))],
        'date': datetime.now().strftime('%d-%m-%y'),
        'numberOfEpisodesComputed': len(episodesNames),
        'engine': chosenEngine,
    }
    if args.name not in lastSession:
        newSessionItem['numberOfEpisodes'] = len(episodesNames)
        newSessionItem['lastep'] = 1
else:
    newSessionItem = {}

def updateList():
    global lastSession
    global newSessionItem
    tmpLastSession = deepcopy(lastSession)
    try:
        for i, key in enumerate(tmpLastSession):
            episodesNumbers = animeInfo('episodesNum', query=key)
            numGoyabu = episodesNumbers['goyabu']
            numAnilist = episodesNumbers['anilist']

            tmpLastSession[key]['numberOfEpisodes'] =  numAnilist
            tmpLastSession[key]['numberOfEpisodesComputed'] =  numGoyabu

            if args.update == False and key == args.name:
                newSessionItem['numberOfEpisodes'] =  numAnilist
                newSessionItem['numberOfEpisodesComputed'] =  numGoyabu
            # simple progress bar
            print(f"[{'-'*i}{' '*(len(tmpLastSession)-i)}]    updating the local list", end='\r')
    except KeyboardInterrupt:
        exit()
    lastSession = tmpLastSession

    print('local list updated'+' '*(len(tmpLastSession)+12))

    if args.player != 'mpv':
        if newSessionItem:
            if args.name in lastSession:
                lastSession[args.name] = {**lastSession[args.name], **newSessionItem}
            else:
                lastSession[args.name] = newSessionItem

        lastSession = {k: lastSession[k] for k in [args.name]+[item for item in lastSession.keys() if item!=args.name]}

        with open(sessionpath, 'w') as rawjson:
            json.dump(lastSession, rawjson)

# Check if mpv is installed
if which('mpv') == None:
    args.player = None

if(args.player == None):
    print('MPV is not installed, please specify an alternative player')
    exit()
elif(args.player == 'mpv'):
    from python_mpv_jsonipc import MPV

    if isWindows:
        mpv = MPV()
    else:
        mpv = MPV(ipc_socket="/tmp/mpv-socket")

    mpvEpIndex = None # Current anime playing 

    # Update last session file with the current anime when the current episode ends
    @mpv.on_event('end-file')
    def end_file_ev(_):
        if mpvEpIndex == None: return
        global newSessionItem
        global lastSession

        newSessionItem['lastep'] = mpvEpIndex
        newSessionItem['engine'] = chosenEngine

        if args.name in lastSession:
            lastSession[args.name] = {**lastSession[args.name],**newSessionItem}
        else:
            lastSession[args.name] = newSessionItem

        lastSession = {k: lastSession[k] for k in [args.name]+[item for item in lastSession.keys() if item!=args.name]}

        with open(sessionpath, 'w') as rawjson:
            json.dump(lastSession, rawjson)

    # Update mpvEpIndex with the current episode every time a new episodes begin
    @mpv.property_observer('media-title')
    def media_title_ob(name, value):
        if type(name) != str or type(value) != str or 'Ep ' not in value: return
        global mpvEpIndex
        mpvEpIndex = int(value.split('-')[0].replace('Ep ', ''))


    # -----
    mpv.playlist_pos = 0
    mpv.play(filepath)
    mpv.command('keypress', 'space')
    sleep(2)
    mpv.command('playlist-play-index', slicelist[0]-1 if slicelist[0] and args.episodes == '' else 0)
    mpv.command('keypress', 'space')
    #  updateList()
elif args.player != 'none':
    os.system(f'{args.player} "{filepath}"')
    updateList()
elif args.player == 'none':
    try:
        if args.update == False:
            runInParallel((serveRawText, fileText), (updateList,))
        else:
            updateList()
    except KeyboardInterrupt:
        exit()

