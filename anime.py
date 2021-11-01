import os, errno
import json
import datetime
from python_mpv_jsonipc import MPV
import termtables as tt
from dropdown import interactiveTable
import time
import argparse
from argparse import RawTextHelpFormatter
from animeScrapper import animeInfo, searchAnime

parser = argparse.ArgumentParser(description='plays anime from terminal', formatter_class=RawTextHelpFormatter)

parser.add_argument('name',          action='store', default='',    type=str, nargs='?',
                    help='anime name')
parser.add_argument('-s','--silent', action='store_true',
                    help='minimal output')
parser.add_argument('-y','--yes',    action='store_true',
                    help='use all default options')
parser.add_argument('--episodes',    action='store', default='',    type=str, metavar='RANGE',
                    help='range of episodes to watch\nformat:  n   - single episode\n         n:n - range of episodes')
parser.add_argument('--player',      action='store', default='mpv', type=str,
                    help='player to run the anime. The default is mpv')

args = parser.parse_args()


slicelist = ['']

if args.episodes:
    slicelist = args.episodes.split(':')
    slicelist.append('')

# read last session file, if don't exist create one
lastSession={}
sessionpath = os.path.join(os.path.dirname(__file__), '.anime-lastsession.json')
if os.path.isfile(sessionpath):
    with open(sessionpath) as rawjson:
        lastSession = json.load(rawjson)
else:
    with open(sessionpath, 'w') as rawjson:
        json.dump({}, rawjson)


# Format last session table, highligthing completed animes
tableVals = [
    [i+1, f'{name} - Episódio {lastSession[name]["lastep"]} [{lastSession[name]["numberOfEpisodes"]}]', lastSession[name]['date']] if lastSession[name]["lastep"] < lastSession[name]['numberOfEpisodes'] else
    [i+1, f'{name} - Completo [{lastSession[name]["numberOfEpisodes"]}]', lastSession[name]['date']] for i,name in enumerate(lastSession)]

staticHighlights = [[i, 'green'] for i,name in enumerate(lastSession) if lastSession[name]['lastep'] >= lastSession[name]['numberOfEpisodes']]

# invert the table to the recently watched animes appears at the bottom 
if len(tableVals) > 1:
    tableVals.reverse()
    staticHighlights = [[len(tableVals)-1-i, color] for i, color in staticHighlights]

# Print the interactive Last Session table
if len(lastSession) and args.name == '':
    results = [[],[],None]

    while len(results[1]) != 1 and results[0] != None:
        results = interactiveTable(tableVals, ["", "Sessões Anteriores", "Data"], "rcc", behaviour='multiSelectWithText', hintText='Nome do Anime[1]: ', staticHighlights=staticHighlights)
        if results[0] == None: continue

        count = 0
        for item in tableVals[::-1]:
            if item[0]==results[0][0]:
                break
            count+=1

        posToRemove = [item[0] for item in results[1][1:]]
        tableVals = [item for i, item in enumerate(tableVals) if i not in posToRemove]
        staticHighlights = [item for item in staticHighlights if item[0] not in posToRemove]


        leftSide = [item for item in staticHighlights if item[0] < count]
        rightSide = [item for item in staticHighlights if item[0] > count]
        staticHighlights = [*leftSide, *[[i-(len(results[1])-1), color] for i,color in rightSide]]


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
        print('Insira um nome válido para continuar\n')
        exit()

#  If users choses one of last session items
if args.name.isdigit() and int(args.name) <= len(lastSession):
    args.name = list(lastSession.keys())[int(args.name)-1]
    slicelist = [str(lastSession[args.name]['lastep']), '']
    args.yes = True

namelist = searchAnime(args.name, engines=['goyabu'])[1]

if len(namelist) == 0:
    print(f'\nNenhum anime com o nome "{args.name}" foi encontrado. Tente outro nome.')
    exit()


# print a interactive table to choose the anime
if  args.yes == False:
    tableVals = [[i+1, namelist[i]] for i in range(len(namelist))]
    result = interactiveTable(tableVals, ["", "Animes"], "rl")
    args.name = result[0][1]


#  sys.stdout.write(f"\033[J")

episodes = animeInfo('episodes', query=args.name)['goyabu']
episodesNames = [name for name,_ in episodes.items()]
videolist = [link for _,link in episodes.items()]

if not args.silent:
    table = tt.to_string(
        [[i+1, episodesNames[i]] for i in range(len(episodesNames))],
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
if all(slicelist) or slicelist[1] != None:
    count = slicelist[0] if slicelist[0] and count == 1 else count
    videolist = videolist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]
    episodesNames = episodesNames[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]


# create the playlist file for the player
fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Episódio {count}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{args.name}.m3u')

if not args.silent: print(f'Salvando em "{filepath}"')

if not os.path.exists(folderpath):
    try:
        os.makedirs(folderpath)
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

with open(filepath, 'w') as writer:
    writer.writelines(fileText)

newSessionItem = {
    #  'episodes': [[namelist[i], videolist[i]] for i in range(len(namelist))],
    'date': datetime.datetime.now().strftime('%d-%m-%y'),
    'numberOfEpisodes': len(episodesNames),
    'lastep': 1
}

#  args.player = 'mpv'
if(args.player == 'mpv'):

    mpv = MPV(ipc_socket="/tmp/mpv-socket")

    mpvEpIndex = None # Current anime playing 

    # Update last session file with the current anime
    @mpv.on_event('end-file')
    def end_file_ev(_):
        if mpvEpIndex == None: return
        global newSessionItem
        global lastSession

        newSessionItem['lastep'] = mpvEpIndex
        lastSession[args.name] = newSessionItem

        lastSession = {k: lastSession[k] for k in [args.name]+[item for item in lastSession.keys() if item!=args.name]}

        with open(sessionpath, 'w') as rawjson:
            json.dump(lastSession, rawjson)

    # Update mpvEpIndex with the current episode
    @mpv.property_observer('media-title')
    def media_title_ob(name, value):
        if type(name) != str or type(value) != str or 'Episódio' not in value: return
        global mpvEpIndex
        mpvEpIndex = int(value.replace('Episódio ', ''))

    # -----
    mpv.playlist_pos = 0
    mpv.play(filepath)
    mpv.command('keypress', 'space')
    time.sleep(2)
    mpv.command('playlist-play-index', slicelist[0]-1 if slicelist[0] else 0)
    mpv.command('keypress', 'space')
else:
    os.system(f'{args.player} "{filepath}"')

for key in lastSession:
    lastSession[key]['numberOfEpisodes'] = animeInfo('episodesNum', query=key)['anilist'] 


        


