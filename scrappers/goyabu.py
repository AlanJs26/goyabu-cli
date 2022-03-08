from typing import Dict, List, Optional, Union
from bs4 import BeautifulSoup as bs4
import requests
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrappers.utils import infoDecorator
#  from utils import infoDecorator

hreflist = []
namelist = []
videolist = []

possibleOutputs = [
    'search',
    'episodes',
    'episodesNum',
    'description',
    'status',
    'cover',
]

def goyabuSearch(name:str) -> List[str]:
    html = requests.get(f'https://goyabu.com/?s={"+".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    global hreflist
    global namelist

    animeList = soup.find(class_='episode-container')
    hreflist = [link['href'] for link in animeList.find_all('a')]
    namelist = [name.text for name in animeList.find_all('h3')]
    
    return namelist

def goyabuDescription(name:str) -> str:
    global namelist
    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        name = namelist[0]

    href = f"https://goyabu.com/assistir/{name.replace(' ', '-')}"

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    description = soup.find_all(class_='anime-description')[0]

    return description.text


def goyabuCover(name:str) -> str:
    global namelist
    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        name = namelist[0]

    href = f"https://goyabu.com/assistir/{name.replace(' ', '-')}"

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')


    img = soup.find_all(class_='anime-cover-left-holder')[0].find_all('img')[0].get('src')

    return img

def goyabuStatus(name:str) -> str:
    global namelist
    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        name = namelist[0]

    href = f"https://goyabu.com/assistir/{name.replace(' ', '-')}"

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    infoEl = soup.find_all(class_='anime-info-right')[0]
    status = infoEl.find_all('div')[4].text
    status = ''.join(status.split(': ')[1:])

    if status == 'Completo':
        status='completed'
    elif status == 'Em lançamento':
        status='releasing'
    else:
        status = 'unknown'

    return status

def goyabuEpisodes(name:str, slicelist=None) -> Dict[str, str]:

    if slicelist == None or type(slicelist) != list or len(slicelist) != 2:
        slicelist = [None, None]
    else:
        slicelist = [int(i) if i.isdigit() else None for i in slicelist]
        slicelist[1] = slicelist[1] and slicelist[1]+1


    global videolist
    global hreflist
    global namelist

    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        href = hreflist[0]
    else:
        href = hreflist[namelist.index(name)]

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    eplist = soup.find(class_='episodes-container')

    ep_hreflist = [ep['href'] for ep in eplist.find_all('a')][slice(*slicelist)]
    ep_idlist = [href[26:-1] for href in ep_hreflist]
    ep_namelist = [name.text for name in eplist.find_all('h3')]
    videolist = ['' for _ in range(len(ep_idlist))]

    def getvideourl(id, i):
        html=requests.get(f'https://goyabu.com/embed.php?id={id}').text 
        allmatches = re.findall(r'(?<=p",file: ").+?(?="[\n\,]?)', html)

        allmatches = list(filter(bool, allmatches))
        if len(allmatches) == 0:
            return 

        videolist[i] = allmatches[0]

    def newGetvideourl(id, i):
        html=requests.get(f'https://goyabu.com/videos/{id}').text 
        allmatches = re.findall(r'(?<=file: ").+(?=")', html)

        allmatches = list(filter(bool, allmatches))
        if len(allmatches) == 0:
            return 

        videolist[i] = allmatches[0]

    with tqdm(total=len(ep_idlist)) as pbar:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(newGetvideourl, id, i) for i,id in enumerate(ep_idlist)]
            for _ in as_completed(futures):
                pbar.update(1)

    return {name:link for name,link in zip(ep_namelist, videolist)}

def goyabuEpisodesNum(name:str) -> int:
    global videolist
    global hreflist
    global namelist

    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        href = hreflist[0] if len(hreflist) else []
    else:
        href = hreflist[namelist.index(name)]

    if href == []: return 0

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    eplist = soup.find(class_='episodes-container')

    ep_hreflist = [ep['href'] for ep in eplist.find_all('a')]

    return len(ep_hreflist)


@infoDecorator(possibleOutputs)
def goyabuInfo(*type:str, query:Optional[str]=None, **kwargs) -> Union[Dict[str, Dict[str, str]], List[str]]:

    global hreflist
    global namelist
    global videolist
    outputs = {}

    if 'episodes' in type and query:
        if 'range' in kwargs:
            outputs['episodes'] = goyabuEpisodes(query, slicelist=kwargs['range'])
        else:
            outputs['episodes'] = goyabuEpisodes(query)

    if 'episodesNum' in type and query:
        outputs['episodesNum'] = goyabuEpisodesNum(query)

    if 'search' in type and query:
        outputs['search'] = goyabuSearch(query)

    if 'description' in type and query:
        outputs['description'] = goyabuDescription(query)

    if 'status' in type and query:
        outputs['status'] = goyabuStatus(query)

    if 'cover' in type and query:
        outputs['cover'] = goyabuCover(query)

    return outputs

if __name__ == "__main__":
    result = goyabuInfo('episodes', query='yuukaku', range=['0','1'])
    print(result)
