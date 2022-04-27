from typing import Callable, Dict, Optional
from scrappers.goyabu import goyabuInfo
from scrappers.aniList import anilistInfo
from scrappers.vizer import vizerInfo
from scrappers.animDl import animdlInfo
from scrappers.animesonline import animesonlineInfo
#  from rich import print

infoAlias: Dict[str, Callable] = {
    'goyabu': goyabuInfo,
    'animesonline': animesonlineInfo,
    'anilist': anilistInfo,
    'vizer': vizerInfo,
    'animdl': animdlInfo,
}

capabilities = {name:info('capabilities') for name, info in infoAlias.items()}
categories = {name:info('category') for name, info in infoAlias.items()}

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

def animeInfo(*types:str, query:Optional[str]=None, engines = searchEngines, **kwargs):
    availableEngines = [key for key, item in capabilities.items() if all(elem in item for elem in types)] 
    availableEngines = list(set(availableEngines).intersection(engines))

    if len(availableEngines) == 0:
        raise SystemExit('any engine can handle these queries')

    outputs = {}

    for engine in availableEngines:
        outputs[engine] = infoAlias[engine](*types, query=query, **kwargs)

    return outputs

def getCapabilityByLanguage(capability:str):
    capabilityByLanguage = {}

    for name, alias in infoAlias.items():
        if capability not in capabilities[name]: continue

        lang = alias('language')
        if lang not in capabilityByLanguage:
            capabilityByLanguage[lang] = [name]
            continue
        capabilityByLanguage[lang].append(name)

    return capabilityByLanguage

#  enginesByLanguage = {}
enginesByLanguage = getCapabilityByLanguage('episodes')

#  for name, alias in infoAlias.items():
    #  if 'episodes' not in capabilities[name]: continue

    #  lang = alias('language')
    #  if lang not in enginesByLanguage:
        #  enginesByLanguage[lang] = [name]
        #  continue
    #  enginesByLanguage[lang].append(name)


#  episodes = filter(lambda x : 'episodes' in capabilities[x], capabilities)

if __name__ == "__main__":
    #  print(searchAnime('boku'))
    #  print(infoAlias['goyabu']('episodes', query='komi'))
    print(animeInfo('episodes', query='shingeki', range=['1', '1']))
    #  print(list(enginesByLanguage))
    #  print(enginesByLanguage)
    #  print(searchAnime('asdffsa'))

    #  print(searchEngines)
    

