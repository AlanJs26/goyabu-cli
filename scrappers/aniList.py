from anilist import Client
from typing import Callable, Dict, List, Optional, Union, overload
from scrappers.utils import infoDecorator

possibleOutputs = [
    'search',
    'episodesNum',
    'status',
    'capabilities'
]

anilistClient = Client()

@infoDecorator(possibleOutputs)
def anilistInfo(*type:str, query:Optional[str]=None) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'capabilities' in type:
        outputs['capabilities'] = possibleOutputs

    if 'search' in type and query:
        rawSearch = anilistClient.search_anime(query, 10)

        outputs['search'] = [item.title.romaji for item in rawSearch] 

    if 'episodesNum' in type and query:
        rawSearch = anilistClient.search_anime(query, 1)

        if len(rawSearch) == 0:
            outputs['episodesNum'] = 0
        else:
            rawSearch = rawSearch[0]

            anime = anilistClient.get_anime(rawSearch.id)

            try:
                episodes = anime.episodes
            except:
                episodes = 12

            outputs['episodesNum'] = episodes


    if 'status' in type and query:
        rawSearch = anilistClient.search_anime(query, 1)

        if len(rawSearch):
            rawSearch = rawSearch[0]

        anime = anilistClient.get_anime(rawSearch.id)
        status = anime.status

        if status == 'FINISHED':
            status='completed'
        elif status == 'AIRING':
            status='releasing'
        else:
            status = 'unknown'

        outputs['status'] = status  

    return outputs

if __name__ == "__main__":
    print(anilistInfo('episodesNum', query='boku'))
    #  anime = anilistClient.get_anime(21234)
    #  print(anime.)
    #  print(dir(anilist))
