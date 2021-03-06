import os, errno
from datetime import datetime,date
import json
import termtables as tt
from dropdown import interactiveTable, bcolors, isWindows
from time import sleep
from argparse import RawTextHelpFormatter, ArgumentParser
from copy import deepcopy
from rawserver import serveRawText
from scrappers.utils import runInParallel, translation, nameTrunc, dir_path 
from shutil import which
from concurrent.futures import ThreadPoolExecutor, as_completed
from locale import getdefaultlocale


sysLang = getdefaultlocale()[0]
if sysLang:
    sysLang = sysLang[0:2] 
else:
    sysLang = 'pt'


usingdefaulteprange = True
def episoderangeparser(string):
    if string == '': return ['', '']
    global usingdefaulteprange
    usingdefaulteprange = False

    slicestring = [*string.split(':'), ''][:2]
    return slicestring

parser = ArgumentParser(description='plays anime from terminal', formatter_class=RawTextHelpFormatter)

parser.add_argument('name',          action='store', default='', type=str, nargs='*',
                    help='anime name')
parser.add_argument('-s','--silent', action='store_true',
                    help='minimal output')
parser.add_argument('-y','--yes',    action='store_true',
                    help='use all default options')
parser.add_argument('--episodes',    action='store', default=['', ''],    type=episoderangeparser, metavar='RANGE',
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

if args.update == True:
    args.player = 'none'
    args.silent = True

args.name = ' '.join(args.name)
chosenEngine = 'goyabu'

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

# Run the m3u8 server
if args.server == True:
    from animeScrapper import searchAnime, enginesByLanguage, capabilities, getCapabilityByLanguage
    from rawserver import generatePlaylist

    animelist = [list(lastSession.keys())[int(anime)] if anime.isdigit() else anime for anime in args.name.split(',')]

    episodeEngines = [key for key, value in capabilities.items() if 'episodes' in value and 'search' in value]

    availableEngines = enginesByLanguage[sysLang] if sysLang in enginesByLanguage else episodeEngines 

    animelist = [searchAnime(anime, engines=availableEngines)[1][0] for anime in animelist]
    playlistText = generatePlaylist(animelist)

    print('Anime Server\n')
    for anime in animelist:
        print(anime)
    print('')

    serveRawText(playlistText)
    exit()

if len(lastSession) == 0 and args.update:
    print('the watch list is empty. Watch a episode first.')
    exit()

# Format last session table, highligthing completed animes
tableVals = []
for i,name in enumerate(lastSession):
    eps = lastSession[name]["numberOfEpisodes"]
    epsComputed = lastSession[name]["numberOfEpisodesComputed"]

    watchDate = lastSession[name]["date"]
    parsedDate = [int(item) for item in watchDate.split('-')]
    diff = datetime.date(datetime.now()) - date(parsedDate[2], parsedDate[1], parsedDate[0])
    watchDate = f'{diff.days} {translation["daysAgo"][sysLang]}'

    lastep = lastSession[name]["lastep"]

    offset = 38

    if lastep == epsComputed and lastep < eps:
        tableVals.append(
[i+1, f'{bcolors["grey"]}{nameTrunc(name, offset+len(name)+len(watchDate))} - Epis??dio {lastep} [{epsComputed}/{eps}]{bcolors["end"]}', watchDate]
        )
    elif lastep < eps:
        tableVals.append(
[i+1, f'{nameTrunc(name, offset+len(name)+len(watchDate))} - Epis??dio {lastep} [{epsComputed}/{eps}]', watchDate]
        )
    else:
        tableVals.append(
[i+1, f'{bcolors["green"]}{nameTrunc(name, offset-5+len(name)+len(watchDate))} - {translation["complete"][sysLang]}{bcolors["end"]}', watchDate]
        )

# Print the interactive Last Session table and remove the selected items
if len(lastSession) and args.name == '' and args.yes == False and args.update == False:
    results = [[],[],None]

    while len(results[1]) != 1 and results[0] != None:
        results = interactiveTable(tableVals[::-1], ["", translation['last_sessions'][sysLang], translation['date'][sysLang]], "rcc", behaviour='multiSelectWithText', maxListSize=17, hintText=translation['hintText'][sysLang], highlightRange=(2,2))
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
            args.name = str(input(translation['inputText'][sysLang]))
        except KeyboardInterrupt:
            exit()

        if args.name == '':
            print(translation['invalidName'][sysLang])
            exit()

from animeScrapper import animeInfo, searchAnime, enginesByLanguage, capabilities, categories, getCapabilityByLanguage

episodeEngines = [key for key, value in capabilities.items() if 'episodes' in value]
episodesNumEngines = [key for key, value in capabilities.items() if 'episodesNum' in value]

availableEngines = enginesByLanguage[sysLang] if sysLang in enginesByLanguage else episodeEngines 
#  if 'episodesNum' in capabilities[availableEngines[0]]:
    #  availableNumEngine = availableEngines[0]
#  else:
    #  availableNumEngine = getCapabilityByLanguage('episodesNum')
    #  availableNumEngine = availableNumEngine[sysLang][0] if sysLang in availableNumEngine else episodesNumEngines[0] 

availableNumEngines = getCapabilityByLanguage('episodesNum')
#  availableNumEngine = availableNumEngine[sysLang][0] if sysLang in availableNumEngine else episodesNumEngines[0] 
availableNumEngines = availableNumEngines[sysLang] if sysLang in availableNumEngines else episodesNumEngines 


#  If users choses one of last session items
if args.name.isdigit() and int(args.name) <= len(lastSession):
    args.name = list(lastSession.keys())[int(args.name)-1]
    args.yes = True
    chosenEngine = lastSession[args.name]['engine']
    if not any(args.episodes):
        args.episodes = [str(lastSession[args.name]['lastep']), '']

if args.update == False:
    rawnamelist = searchAnime(args.name, engines=availableEngines)[0]
    namelist = []
    for engine in rawnamelist:
        for item in rawnamelist[engine]:
            namelist.append([item, engine])

    if args.yes:
        args.name = namelist[0][0]
        chosenEngine = namelist[0][1]
else:
    namelist = []

if len(namelist) == 0 and args.update == False:
    print(translation['animeNotFound'][sysLang].format(args.name))
    exit()

# print a interactive table to choose the anime
if  args.yes == False and args.update == False:

    mergednamelist = []
    verifiednames = []

    for item, engine in namelist:
        if item in verifiednames:
            continue

        accumEngines = [engine]
        verifiednames.append(item)

        for inneritem, innerengine in namelist:
            if inneritem == item and engine != innerengine:
                accumEngines.append(innerengine)
        mergednamelist.append([item, accumEngines])

    tableValsOrig = [[i+1,           title,                 ', '.join(engineNames)] for i, (title, engineNames) in enumerate(mergednamelist)]
    tableVals     = [[i+1, nameTrunc(title, 15+len(title)), ', '.join(engineNames)] for i, (title, engineNames) in enumerate(mergednamelist)]

    result = interactiveTable(tableVals, ["", "Anime", "engine"], "rll", maxListSize=17, highlightRange=(2,2))
    args.name = tableValsOrig[result[0][0]-1][1]
    chosenEngine = result[0][-1]

    if len(chosenEngine.split(', '))>1:
        result = interactiveTable([[engine] for engine in chosenEngine.split(', ')], ["engine"], "l", maxListSize=17, highlightRange=(0,1))
        chosenEngine = result[0][-1]


if args.update == False:
    #  episodes = animeInfo('episodes', query=args.name)['goyabu', 'vizer']
    if any(args.episodes) and usingdefaulteprange == False:
        episodes = animeInfo('episodes', query=args.name, range=args.episodes, engines=[chosenEngine])[chosenEngine]
    else:
        episodes = animeInfo('episodes', query=args.name, engines=[chosenEngine])[chosenEngine]
    episodesNames = [*episodes.keys()]
    videolist = [*episodes.values()]
else: 
    episodes = []
    episodesNames = []
    videolist = []

if not args.silent:
    table = tt.to_string(
        [[i+1, nameTrunc(episodesNames[i], len(episodesNames[i])+15)] for i in range(len(episodesNames))],
        header=["",translation['episodes'][sysLang]],
        style=tt.styles.rounded,
        alignment="rl",
    )
    table = table.split('\n')
    print('\n'.join(table[0:3]+table[1::2][1:]+table[-1:]))


if not any(args.episodes):
    if not args.silent:
        print(translation['sliceHelp'][sysLang])
    try:
        args.episodes = str(input(translation['sliceHint'][sysLang])).split(':') if not args.yes else ['todos']
        args.episodes.append('')
    except KeyboardInterrupt:
        print('')
        os._exit(0)


# extract the choosen range from the fetched lists
count = 1
args.episodes = [int(i) if i.isdigit() else None for i in args.episodes]
if any(args.episodes) and usingdefaulteprange == False and args.update == False:
    count = args.episodes[0] or count

    #  videolist     =     videolist[slice(args.episodes[0], args.episodes[1]+1 if args.episodes[1] else None)]
    #  episodesNames = episodesNames[slice(args.episodes[0], args.episodes[1]+1 if args.episodes[1] else None)]


# create the playlist file for the player
fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Ep {count} - {args.name}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{args.name}.m3u')

if not args.silent: print(translation['savingIn'][sysLang].format(filepath))

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
        'date': datetime.now().strftime('%d-%m-%Y'),
        'numberOfEpisodesComputed': len(episodesNames) if usingdefaulteprange else animeInfo('episodesNum', query=args.name, engines=[chosenEngine])[chosenEngine],
        'engine': chosenEngine,
    }
    if args.name not in lastSession:
        newSessionItem['numberOfEpisodes'] = len(episodesNames)
        newSessionItem['lastep'] = 1
else:
    newSessionItem = {}


def updateListSynchronous():
    global lastSession
    global newSessionItem
    tmpLastSession = deepcopy(lastSession)
    try:
        for i,key in enumerate(tmpLastSession):
            episodesNumbers = animeInfo('episodesNum', query=key, engines=[*availableNumEngines, 'anilist'])
            currentcategory = categories[tmpLastSession[key]['engine']]

            validEngine = ''
            for engine, num in episodesNumbers.items():
                if num>0 and engine != 'anilist' and categories[engine] == categories[tmpLastSession[key]['engine']]:
                    validEngine = engine
                    break
            
            numChosenEngine = episodesNumbers[validEngine or availableNumEngines[0]]
            numAnilist = episodesNumbers['anilist']

            tmpLastSession[key]['numberOfEpisodes'] =  numAnilist if currentcategory == 'anime' else numChosenEngine 
            tmpLastSession[key]['numberOfEpisodesComputed'] =  numChosenEngine

            if args.update == False and key == args.name:
                newSessionItem['numberOfEpisodes'] =  numAnilist if currentcategory == 'anime' else numChosenEngine
                newSessionItem['numberOfEpisodesComputed'] =  numChosenEngine
            # simple progress bar

            print(f"\033[K[{'-'*i}{' '*(len(tmpLastSession)-i)}]   {translation['listUpdating'][sysLang]}", end='\r')           

    except KeyboardInterrupt:
        exit()
    lastSession = tmpLastSession

    print(translation['listUpdated'][sysLang]+' '*(len(tmpLastSession)+12))

    if args.player != 'mpv':
        if newSessionItem:
            if args.name in lastSession:
                lastSession[args.name] = {**lastSession[args.name], **newSessionItem}
            else:
                lastSession[args.name] = newSessionItem

        lastSession = {k: lastSession[k] for k in [args.name]+[item for item in lastSession.keys() if item!=args.name]}

        with open(sessionpath, 'w') as rawjson:
            json.dump(lastSession, rawjson)

finishedWorkers = 0
def updateList():
    global lastSession
    global newSessionItem
    tmpLastSession = deepcopy(lastSession)
    try:
        def updateWorker(key):
            global finishedWorkers
            episodesNumbers = animeInfo('episodesNum', query=key, engines=[*availableNumEngines, 'anilist'])
            currentcategory = categories[tmpLastSession[key]['engine']]

            validEngine = ''
            for engine, num in episodesNumbers.items():
                if num>0 and engine != 'anilist' and categories[engine] == categories[tmpLastSession[key]['engine']]:
                    validEngine = engine
                    break
            
            numChosenEngine = episodesNumbers[validEngine or availableNumEngines[0]]
            numAnilist = episodesNumbers['anilist']

            tmpLastSession[key]['numberOfEpisodes'] =  numAnilist if currentcategory == 'anime' else numChosenEngine 
            tmpLastSession[key]['numberOfEpisodesComputed'] =  numChosenEngine

            if args.update == False and key == args.name:
                newSessionItem['numberOfEpisodes'] =  numAnilist if currentcategory == 'anime' else numChosenEngine
                newSessionItem['numberOfEpisodesComputed'] =  numChosenEngine
            # simple progress bar
            finishedWorkers+=1

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(updateWorker, key) for _,key in enumerate(tmpLastSession)]
            for _ in as_completed(futures):
                print(f"\033[K[{'-'*finishedWorkers}{' '*(len(tmpLastSession)-finishedWorkers)}]    {translation['listUpdating'][sysLang]}", end='\r')           

    except KeyboardInterrupt:
        exit()
    lastSession = tmpLastSession

    print(translation['listUpdated'][sysLang]+' '*(len(tmpLastSession)+12))

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
if which('mpv') == None and args.player != 'none':
    args.player = None

if(args.player == None ):
    print(translation['mpvNotFound'][sysLang])
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
    mpv.command('playlist-play-index', args.episodes[0]-1 if args.episodes[0] and usingdefaulteprange else 0)
    mpv.command('keypress', 'space')
    if args.synch == True:
        updateListSynchronous()
    else:
        updateList()
elif args.player != 'none':
    os.system(f'{args.player} "{filepath}"')
    if args.synch == True:
        updateListSynchronous()
    else:
        updateList()
elif args.player == 'none':
    try:
        if args.update == False:
            runInParallel((serveRawText, fileText), (updateList,))
        elif args.synch == True:
            updateListSynchronous()
        else:
            updateList()
    except KeyboardInterrupt:
        exit()
