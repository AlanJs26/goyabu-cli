#  from './scrappers/goyabu.py' import goyabuSearch
from typing import Callable, Dict, List, Optional
from scrappers.goyabu import goyabuInfo
from scrappers.aniList import anilistInfo

infoAlias: Dict[str, Callable] = {
    'goyabu': goyabuInfo,
    'anilist': anilistInfo,
}

capabilities = {name:info('capabilities') for name, info in infoAlias.items()}

#  searchEnginesAliases: Dict[str, Callable] = {name:info('searchFunc') for name, info in infoAlias.items()}

searchEngines = [key for key, value in capabilities.items() if 'search' in value]

def searchAnime(name:str, engines = searchEngines):
    difference = list(set(engines).difference(searchEngines))
    if len(difference)>1:
        raise SystemExit(f"{' and '.join(difference)} are not valid search engines")
    elif len(difference):
        raise SystemExit(f"{difference[0]} isn't a valid search engine")

    foundAnimesByEngine = {}

    for engine in engines:
        foundAnimesByEngine[engine] = infoAlias[engine]('search', query=name)

    foundAnimes = []

    for key in foundAnimesByEngine:
        for item in foundAnimesByEngine[key]:
            foundAnimes.append(item)

    foundAnimes = list(set(foundAnimes))

    return foundAnimesByEngine, foundAnimes

def animeInfo(*types:str, query:Optional[str]=None, engines = searchEngines):
    availableEngines = [key for key, item in capabilities.items() if all(elem in item for elem in types)] 
    availableEngines = list(set(availableEngines).intersection(engines))

    if len(availableEngines) == 0:
        raise SystemExit('any engine can handle these queries')

    outputs = {}

    for engine in availableEngines:
        outputs[engine] = infoAlias[engine](*types, query=query)

    return outputs


if __name__ == "__main__":
    #  print(searchAnime('boku'))
    #  print(infoAlias['goyabu']('episodes', query='komi'))
    print(animeInfo('episodesNum', query='boku', engines=['anilist']))
    #  print(searchAnime('asdffsa'))

    #  print(searchEngines)
    

