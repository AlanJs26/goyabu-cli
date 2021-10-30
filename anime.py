import os, errno
import re
import requests
from bs4 import BeautifulSoup as bs4
import json
import datetime
from python_mpv_jsonipc import MPV
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
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
    [i+1, f'{name} - Episódio {lastSession[name]["lastep"]}', lastSession[name]['date']] if lastSession[name]["lastep"] < lastSession[name]['numberOfEpisodes'] else
    [i+1, f'{name} - Completo', lastSession[name]['date']] for i,name in enumerate(lastSession)]

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

    #  table = interactiveTable(tableVals, ["", "Sessões Anteriores", "Data"], "rcc", behaviour='multiSelectWithText', hintText='Nome do Anime: ', staticHighlights=staticHighlights)

#  If the search term is empty and exists last session items, choose the first last session
if args.name == '':
    if len(lastSession):
        args.name = '1'
    else:
        print('Insira um nome válido para continuar\n')
        os._exit(0)

#  If users choses one of last session items
if args.name.isdigit() and int(args.name) <= len(lastSession):
    args.name = list(lastSession.keys())[int(args.name)-1]
    slicelist = [str(lastSession[args.name]['lastep']), '']
    args.yes = True


html = requests.get(f'https://goyabu.com/?s={"+".join(args.name.split(" "))}').text
soup = bs4(html, 'html.parser')

eplist = soup.find(class_='episode-container')
hreflist = [ep['href'] for ep in eplist.find_all('a')]
namelist = [name.text for name in eplist.find_all('h3')]

if len(namelist) == 0:
    print(f'\nNenhum anime com o nome "{args.name}" foi encontrado. Tente outro nome.')
    os._exit(0)

chosenId = '1'

# print a interactive table to choose the anime
if  args.yes == False:
    tableVals = [[i+1, namelist[i]] for i in range(len(namelist))]
    result = interactiveTable(tableVals, ["", "Animes"], "rl")
    chosenId = str(result[0][0]) 


#  sys.stdout.write(f"\033[J")

chosenId = 1 if not chosenId.isdigit() else int(chosenId)
chosenhref = hreflist[chosenId-1]
chosenName = namelist[chosenId-1]

html = requests.get(chosenhref).text
soup = bs4(html, 'html.parser')

def getvideourl(url, id):
    html=requests.get(url).text 
    allmatches = re.findall(r"(?<=<source).+?src='(.*?)(?='\s+?/>)", html)
    morematches = re.findall(r"file: \"(.+?)\"}", html)
    allmatches = allmatches+morematches

    allmatches = [match for match in allmatches if match != '']
    if len(allmatches) == 0:
        return 
    global videolist
    videolist[id] = allmatches[-1]


eplist = soup.find(class_='episodes-container')

hreflist = [ep['href'] for ep in eplist.find_all('a')]
idlist = [href[26:-1] for href in hreflist]
namelist = [name.text for name in eplist.find_all('h3')]
count = 1
videolist = ['' for _ in range(len(idlist))]

with tqdm(total=len(idlist)) as pbar:
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(getvideourl, f'https://goyabu.com/embed.php?id={id}', i) for i,id in enumerate(idlist)]
        for _ in as_completed(futures):
            pbar.update(1)

if not args.silent:
    table = tt.to_string(
        [[i+1, namelist[i]] for i in range(len(namelist))],
        header=["","Episódios"],
        style=tt.styles.rounded,
        alignment="rl",
    )
    table = table.split('\n')
    print('\n'.join(table[0:3]+table[1::2][1:]+table[-1:]))


if slicelist == ['']:
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
slicelist = [int(i) if i.isdigit() else None for i in slicelist]
if all(slicelist) or slicelist[1] != None:
    count = slicelist[0] if slicelist[0] and count == 1 else count
    videolist = videolist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]
    namelist = namelist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]


# create the playlist file for the player
fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Episódio {count}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{chosenName}.m3u')

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
    'numberOfEpisodes': len(namelist),
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
        lastSession[chosenName] = newSessionItem

        lastSession = {k: lastSession[k] for k in [chosenName]+[item for item in lastSession.keys() if item!=chosenName]}

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
    #  print(slicelist)
    #  mpv.playlist_pos = slicelist[0] if any(slicelist) else 0 
    time.sleep(2)
    mpv.command('playlist-play-index', slicelist[0]-1 if slicelist[0] else 0)
    mpv.command('keypress', 'space')
    # mpv.volume = 10
else:
    os.system(f'{args.player} "{filepath}"')


        


