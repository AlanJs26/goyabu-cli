import re
from typing import Dict, List, Optional, Union
# from tqdm import tqdm
import requests

from utils import infoDecorator
from old_scrapers.goyabu import goyabuEpisodesNum

# from utils import infoDecorator
# from goyabu import goyabuEpisodesNum

#  from rich import print


import logging
from animdl.core.cli.helpers.processors import process_query
from animdl.core.cli.helpers.searcher import link 
from animdl.core.cli.helpers import ensure_extraction, get_check
from animdl.core.cli.http_client import client
#  from animdl.core.config import DEFAULT_PROVIDER
from animdl.core.codebase import providers

possibleOutputs = [
    'search',
    'episodes',
    'episodesNum',
    'language',
    'category'

]

session = client

linksBuffer = []
searchBuffer = {}


def animdlSearch(name:str) -> List[Dict[str,str]]:
    global searchBuffer
    genexp = link.get('animixplay')(session, name)

    search_results = [item for item in genexp]

    searchBuffer = {i['name']:i['anime_url'] for i in search_results}

    return search_results

def animdlEpisodesNum(name:str) -> int:
    global linksBuffer
    if linksBuffer:
        return len(linksBuffer)

    return goyabuEpisodesNum(name) 

def animdlEpisodes(name:str, anime_url=None, slicelist=None) -> Dict[str, str]: 

    if slicelist == None or type(slicelist) != list or len(slicelist) != 2:
        slicelist = ['', '']
    else:
        slicelist = [str(i) if i!=None else '' for i in slicelist]

    global linksBuffer

    episodesNum = goyabuEpisodesNum(name)

    if name in searchBuffer:
        anime_url = searchBuffer[name]

    if anime_url == None:
        logger = logging.getLogger('grabber')
        anime, __provider__ = process_query(
            session, name, logger, provider='animixplay', auto=True)
        anime_url = anime.get('anime_url')
        name = anime.get('name')

    links = {}

    # with tqdm(total=episodesNum) as pbar:
    for stream_url_caller, episode in providers.get_appropriate(session, anime_url, check=get_check(':'.join(slicelist))):
        stream_url = list(ensure_extraction(session, stream_url_caller))

        #  print(f'"{stream_url}" --- "{episode}"')

        playlistfile = requests.get(stream_url[-1]['stream_url']).text

        matches = re.findall(r"RESOLUTION=(?P<w>\d+)x(?P<h>\d+).+\n(?P<link>.+)", playlistfile)

        sorted_by_resolution = sorted(matches, key=lambda i:int(i[0])*int(i[1]))

        links[f'{name} - {episode}'] = sorted_by_resolution[-1][2]

            # pbar.update(1)

    linksBuffer = {**links}

    return links




@infoDecorator(possibleOutputs)
def animdlInfo(*type:str, query:Optional[str]=None, **kwargs) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'search' in type and query:
        outputs['search'] = [anime['name'] for anime in animdlSearch(query)] 

    if 'episodesNum' in type and query:
        outputs['episodesNum'] = animdlEpisodesNum(query)

    if 'episodes' in type and query:
        if 'range' in kwargs:
            outputs['episodes'] = animdlEpisodes(query, slicelist=kwargs['range']) 
        else:
            outputs['episodes'] = animdlEpisodes(query) 

    if 'language' in type:
        outputs['language'] = 'en'

    if 'category' in type:
        outputs['category'] = 'anime'

    return outputs

if __name__ == "__main__":

    #  results = animdlSearch('yuukaku')
    #  print(results)

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

    # results = animdlEpisodes('yuukaku')
    # print(results)

