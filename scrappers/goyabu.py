from typing import Dict, List, Optional, Union
from difflib import SequenceMatcher
from bs4 import BeautifulSoup as bs4
import requests
import re
# from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrappers.utils import infoDecorator
# from utils import infoDecorator


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
    'language',
    'category'

]

def goyabuSearch(name:str) -> List[str]:
    html = requests.get(f'https://goyabu.com/?s={"+".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    global hreflist
    global namelist

    animeList = soup.find(class_='episodes-container')
    results = zip([link['href'] for link in animeList.find_all('a')], [name.text for name in animeList.find_all('h3')])
    results = sorted(results, key=lambda x: SequenceMatcher(None, name, x[1]).ratio(), reverse=True)

    hreflist, namelist = [[name for name, _    in results],
                          [href for _   , href in results]]
    
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

    if slicelist == None or type(slicelist) != list or len(slicelist) > 2 or len(slicelist) == 0:
        slicelist = [None, None]
    elif len(slicelist) == 1:
        slicelist[0] = int(slicelist[0]) if slicelist[0].isdigit() else None
        slicelist.append(int(slicelist[0])+1 if slicelist else None)
    else:
        slicelist = [int(i) if i.isdigit() else None for i in slicelist]
        #  slicelist[1] = slicelist[1] and slicelist[1]+1



    global videolist
    global hreflist
    global namelist

    if len(namelist) == 0 or name not in namelist:
        goyabuSearch(name)
        matched = list(filter(lambda x:x==name, hreflist))
        print(matched)
        href = matched[0] if len(matched) else hreflist[0]
    else:
        href = hreflist[namelist.index(name)]
        print(namelist.index(name))

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    eplist = soup.find(class_='episodes-container')

    ep_hreflist = [ep['href'] for ep in eplist.find_all('a')][slice(*slicelist)]
    ep_idlist = [href[26:-1] for href in ep_hreflist]
    ep_namelist = [name.text for name in eplist.find_all('h3')][slice(*slicelist)]
    videolist = ['' for _ in range(len(ep_idlist))]

    def getvideourl(id, i):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

        html=requests.get(f'https://goyabu.com/videos/{id}', headers=headers).text 
        #  allmatches = re.findall(r'(?<=file: ").+(?=")', html)
        allmatches = re.findall(r"(?<=src=').+kanra\.dev.+?(?=')", html)

        allmatches = list(filter(bool, allmatches))
        if len(allmatches) == 0:
            return 

        videolist[i] = allmatches[0]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(getvideourl, id, i) for i,id in enumerate(ep_idlist)]
    # with tqdm(total=len(ep_idlist)) as pbar:
    #     with ThreadPoolExecutor(max_workers=3) as executor:
    #         futures = [executor.submit(getvideourl, id, i) for i,id in enumerate(ep_idlist)]
    #         for _ in as_completed(futures):
    #             pbar.update(1)

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

    if 'language' in type:
        outputs['language'] = 'pt'

    if 'category' in type:
        outputs['category'] = 'anime'

    return outputs

if __name__ == "__main__":
    #  result = goyabuInfo('episodes', query='yuukaku', range=['3'])
    # result = goyabuInfo('episodes', query='yuukaku')
    # print(result)

    import termtables as tt
    from dropdown import interactiveTable, bcolors, isWindows
    tablelist = [
        ['episodio 1','episodio 1', 'um'  ],
        ['episodio 2','episodio 2', 'dois'  ],
        ['episodio 3','episodio 3', 'tres'  ],
        ['episodio 4','episodio 4', 'quatro'  ],
        ['episodio 4','episodio 4', 'quatro'  ],
        ['episodio 5','episodio 5', 'cinco'  ],
        ['episodio 6','episodio 6', 'seis'   ],
        ['episodio 7','episodio 7', 'sete'   ],
        ['episodio 8','episodio 8', 'oito'],
        ['episodio 5','episodio 5', 'cinco'  ],
        ['episodio 6','episodio 6', 'seis'   ],
        ['episodio 7','episodio 7', 'sete'   ],
        ['episodio 8','episodio 8', 'oito'],
    ]
    interactiveTable(tablelist, ['' ,"Episódios", "Nome"], "rcc", behaviour='multiSelectWithText',maxListSize=7, highlightRange=(2,2))

