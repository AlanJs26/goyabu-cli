import re
from typing import Callable, Dict, List, Optional, Tuple, Union, overload
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from scrappers.utils import infoDecorator
from scrappers.goyabu import goyabuEpisodesNum

#  from utils import infoDecorator
#  from goyabu import goyabuEpisodesNum

#  from rich import print


import logging
from animdl.core.cli.helpers.processors import process_query
from animdl.core.cli.helpers.searcher import link 
from animdl.core.cli.helpers import ensure_extraction, get_check
from animdl.core.cli.http_client import client
from animdl.core.config import DEFAULT_PROVIDER
from animdl.core.codebase import providers

possibleOutputs = [
    'search',
    'episodes',
    'episodesNum',
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
        anime, provider = process_query(
            session, name, logger, auto=None, auto_index=None)
        #  print(anime.get('name'))
        #  print("{}/{}".format(provider, logger.name))
        #  print("Initializing grabbing session.")
        anime_url = anime.get('anime_url')
        name = anime.get('name')

    links = {}

    with tqdm(total=episodesNum) as pbar:
        for stream_url_caller, episode in providers.get_appropriate(session, anime_url, check=get_check(':'.join(slicelist))):
            stream_url = list(ensure_extraction(session, stream_url_caller))

            #  print(f'"{stream_url}" --- "{episode}"')

            playlistfile = requests.get(stream_url[-1]['stream_url']).text

            matches = re.findall(r"RESOLUTION=(?P<w>\d+)x(?P<h>\d+).+\n(?P<link>.+)", playlistfile)

            sorted_by_resolution = sorted(matches, key=lambda i:int(i[0])*int(i[1]))

            links[f'{name} - {episode}'] = sorted_by_resolution[-1][2]

            pbar.update(1)

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

    return outputs

if __name__ == "__main__":

    results = animdlSearch('yuukaku')
    print(results)

    results = animdlEpisodes(results[0]['name'], results[0]['anime_url'])
    print(results)

