import re
import requests
from bs4 import BeautifulSoup as bs4
import termtables as tt
import os
import sys
import errno

args = sys.argv[1:]

searchterm = ''

if len(args)>=1 and args[0] not in ['-y', '-s', '--silent', '-e']:
    searchterm = args[0]

if searchterm == '': 
    searchterm = str(input('Nome do Anime: '))

yesall = True if '-y' in args else False

html = requests.get(f'https://goyabu.com/?s={"+".join(searchterm.split(" "))}').text
soup = bs4(html, 'html.parser')

eplist = soup.find(class_='episode-container')
hreflist = [ep['href'] for ep in eplist.find_all('a')]
namelist = [name.text for name in eplist.find_all('h3')]

if len(namelist) == 0:
    print(f'\nNenhum anime com o nome "{searchterm}" foi encontrado. Tente outro nome.')
    exit()

table = tt.to_string(
    [[i+1, namelist[i]] for i in range(len(namelist))],
    header=["Id", "Nome"],
    style=tt.styles.rounded,
    alignment="rl",
)
table = table.split('\n')
print('\n'.join(table[0:2]+[table[2]]+table[1::2][1:]+table[-1:]))

chosenId = str(input('Escolha o anime pelo Id [1]: ')) if not yesall else '1'
chosenId = 1 if not chosenId.isdigit() else int(chosenId)
chosenhref = hreflist[chosenId-1]
chosenName = namelist[chosenId-1]

print('')

html = requests.get(chosenhref).text
soup = bs4(html, 'html.parser')

def getvideourl(url):
    html=requests.get(url).text 
    allmatches = re.findall(r"(?<=<source).+?src='(.*?)(?='\s+?/>)", html)
    morematches = re.findall(r"file: \"(.+?)\"}", html)
    allmatches = allmatches+morematches

    allmatches = [match for match in allmatches if match != '']
    if len(allmatches) == 0:
        return ''
    return allmatches[-1]

eplist = soup.find(class_='episodes-container')
hreflist = [ep['href'] for ep in eplist.find_all('a')]
idlist = [href[26:-1] for href in hreflist]
namelist = [name.text for name in eplist.find_all('h3')]
videolist = [getvideourl(f'https://goyabu.com/embed.php?id={idnum}') for idnum in idlist]

table = tt.to_string(
    [[i+1, namelist[i]] for i in range(len(namelist))],
    header=["Id","Nome"],
    style=tt.styles.rounded,
    alignment="rl",
)
table = table.split('\n')
print('\n'.join(table[0:3]+table[1::2][1:]+table[-1:]))

slicelist = ['']

if '-e' in args:
    index = args.index('-e')
    if len(args) > index+1:
        slicelist = args[index+1].split(':')

if slicelist == ['']:
    print('''
    n - único episódio
    n:n - intervalo de episódios
    todos - todos os episódios
    ''')
    slicelist = str(input('Episódios para assistir [todos]: ')).split(':') if not yesall else ['todos']

count = 1

if(len(slicelist)==1 and slicelist[0].isdigit() and int(slicelist[0])<len(videolist) and int(slicelist[0])>0):
    count = int(slicelist[0])
    videolist = [videolist[int(slicelist[0])-1]]
elif(len(slicelist)>1 and slicelist[0].isdigit() and slicelist[1].isdigit() and int(slicelist[0])<len(videolist)) and int(slicelist[1])<len(videolist) and int(slicelist[0])>0 and int(slicelist[1])>0:
    count = int(slicelist[0])
    videolist = videolist[int(slicelist[0]):int(slicelist[1])+1]

fileText = '#EXTM3U\n\n'
for video in videolist:
    fileText+=f'#EXTINF:-1,Episódio {count}\n'
    fileText+=f'{video}\n\n'
    count=count+1

folderpath = os.path.join(os.path.expanduser('~'), "Downloads/anime-playlists/")
filepath = os.path.join(folderpath, f'{chosenName}.m3u')

print(f'Salvando em "{folderpath}"')

if not os.path.exists(folderpath):
    try:
        os.makedirs(folderpath)
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

with open(filepath, 'w') as writer:
    writer.writelines(fileText)

foundsilent = -1

if '-s' in args:
    foundsilent = args.index('-s')
if '--silent' in args:
    foundsilent = args.index('--silent')

player = 'mpv'
if('--play' in args):
    index = args.index('--play')
    if len(args) > index+1:
        player = args[index+1]
    os.system(f'{player} "{filepath}"')
elif(foundsilent == -1):
    os.system(f'{player} --no-terminal "{filepath}"')

