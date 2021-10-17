import re
import requests
from bs4 import BeautifulSoup as bs4
import termtables as tt
import os
import sys
import errno
import json
import datetime
from python_mpv_jsonipc import MPV
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

mpv = MPV(ipc_socket="/tmp/mpv-socket")

args = sys.argv[1:]
slicelist = ['']
yesall = True if '-y' in args else False
searchterm = ''
silent = ('-s' in args or '--silent' in args)

if '-e' in args:
    index = args.index('-e')
    if len(args) > index+1:
        slicelist = args[index+1].split(':')
        slicelist.append('')

lastSession={}
sessionpath = os.path.join(os.path.dirname(__file__), '.anime-lastsession.json')
if os.path.isfile(sessionpath):
    with open(sessionpath) as rawjson:
        lastSession = json.load(rawjson)
else:
    with open(sessionpath, 'w') as rawjson:
        json.dump({}, rawjson)
tableVals = [[i+1, f'{name} - Episódio {lastSession[name]["lastep"]}', lastSession[name]['date']] for i,name in enumerate(lastSession)]
if len(tableVals) > 1: tableVals.reverse()
if len(lastSession) and not silent:
    table = tt.to_string(
        tableVals,
        header=["", "Sessões Anteriores", "Data"],
        style=tt.styles.rounded,
        alignment="rcc",
    )
    table = table.split('\n')
    print('\n'.join(table[0:2]+[table[2]]+table[1::2][1:]+table[-1:]))

if len(args)>=1 and args[0] not in ['-y', '-s', '--silent', '-e']:
    searchterm = args[0]

if searchterm == '': 
    try:
        searchterm = str(input(f'Nome do Anime:{"[1]:" if len(lastSession) else ""} '))
    except KeyboardInterrupt:
        print('')
        exit()

if searchterm == '':
    if len(lastSession):
        searchterm = '1'
    else:
        print('Insira um nome válido para continuar\n')
        exit()

if searchterm.isdigit() and int(searchterm) <= len(lastSession):
    searchterm = list(lastSession.keys())[int(searchterm)-1]
    slicelist = [str(lastSession[searchterm]['lastep']), '']
    yesall = True



html = requests.get(f'https://goyabu.com/?s={"+".join(searchterm.split(" "))}').text
soup = bs4(html, 'html.parser')

eplist = soup.find(class_='episode-container')
hreflist = [ep['href'] for ep in eplist.find_all('a')]
namelist = [name.text for name in eplist.find_all('h3')]

if len(namelist) == 0:
    print(f'\nNenhum anime com o nome "{searchterm}" foi encontrado. Tente outro nome.')
    exit()

if not silent:
    table = tt.to_string(
        [[i+1, namelist[i]] for i in range(len(namelist))],
        header=["", "Animes"],
        style=tt.styles.rounded,
        alignment="rl",
    )
    table = table.split('\n')
    print('\n'.join(table[0:2]+[table[2]]+table[1::2][1:]+table[-1:]))


chosenid = '1'
try:
    chosenId = str(input('Escolha o anime pelo Id [1]: ')) if not yesall else '1'
except KeyboardInterrupt:
    print('')
    exit()
chosenId = 1 if not chosenId.isdigit() else int(chosenId)
chosenhref = hreflist[chosenId-1]
chosenName = namelist[chosenId-1]

print('')

html = requests.get(chosenhref).text
soup = bs4(html, 'html.parser')

def getvideourl(url, id):
    html=requests.get(url).text 
    allmatches = re.findall(r"(?<=<source).+?src='(.*?)(?='\s+?/>)", html)
    morematches = re.findall(r"file: \"(.+?)\"}", html)
    allmatches = allmatches+morematches

    allmatches = [match for match in allmatches if match != '']
    if len(allmatches) == 0:
        # return ''
        return 
    global videolist
    # videolist[id] = [allmatches[-1], id]
    videolist[id] = allmatches[-1]
    # print(id)
    # return allmatches[-1]


eplist = soup.find(class_='episodes-container')

if slicelist != [''] and slicelist != None:
    slicelistParsed = [int(i) if i.isdigit() else None for i in slicelist]
    namelist = [name.text for name in eplist.find_all('h3')][slice(slicelistParsed[0]-1, slicelistParsed[1]+1 if slicelistParsed[1] else None)]
    hreflist = [ep['href'] for ep in eplist.find_all('a')][slice(slicelistParsed[0]-1, slicelistParsed[1]+1 if slicelistParsed[1] else None)]
    idlist = [href[26:-1] for href in hreflist]
    videolist = ['' for _ in range(len(idlist))]
    count = slicelistParsed[0]
    slicelist=['']
else:
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

# videolist = [item[0] for item in videolist]
# videolist = [getvideourl(f'https://goyabu.com/embed.php?id={idnum}') for idnum in idlist]

if not silent:
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
        slicelist = str(input('Episódios para assistir [todos]: ')).split(':') if not yesall else ['todos']
        slicelist.append('')
    except KeyboardInterrupt:
        print('')
        exit()


slicelist = [int(i) if i.isdigit() else None for i in slicelist]
count =slicelist[0] if slicelist[0] and count == 1 else count
videolist = videolist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]
namelist = namelist[slice(slicelist[0], slicelist[1]+1 if slicelist[1] else None)]

fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Episódio {count}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{chosenName}.m3u')

if not silent: print(f'Salvando em "{folderpath}"')

if not os.path.exists(folderpath):
    try:
        os.makedirs(folderpath)
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

with open(filepath, 'w') as writer:
    writer.writelines(fileText)

newSessionItem = {
    'episodes': [[namelist[i], videolist[i]] for i in range(len(namelist))],
    'date': datetime.datetime.now().strftime('%d-%m-%y'),
    'lastep': 1
}

mpvEpIndex = None
@mpv.on_event('end-file')
def end_file_ev(_):
    global newSessionItem
    global lastSession
    if mpvEpIndex != None:
        newSessionItem['lastep'] = mpvEpIndex
        lastSession[chosenName] = newSessionItem

        lastSession = {k: lastSession[k] for k in [chosenName]+[item for item in lastSession.keys() if item!=chosenName]}

        with open(sessionpath, 'w') as rawjson:
            json.dump(lastSession, rawjson)

@mpv.property_observer('media-title')
def media_title_ob(name, value):
    if type(name) != str or type(value) != str or 'Episódio' not in value: return
    global mpvEpIndex
    mpvEpIndex = int(value.replace('Episódio ', ''))

player = 'mpv'
if('--play' in args):
    index = args.index('--play')
    if len(args) > index+1:
        player = args[index+1]

    os.system(f'{player} "{filepath}"')
    mpv.terminate()
else:
    mpv.play(filepath)
    mpv.playlist_pos = 0
    # mpv.volume = 10


        


