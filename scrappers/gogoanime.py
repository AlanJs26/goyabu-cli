
from typing import Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup as bs4
import requests

#  from scrappers.utils import infoDecorator
from utils import infoDecorator
#  from rich import print

possibleOutputs = [
    'search',
    'episodes',
]


@infoDecorator(possibleOutputs)
def gogoanimeInfo(*type:str, query:Optional[str]=None) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    #  if 'search' in type and query:
        #  outputs['search'] = [item[0] for item in gogoanimeSearch(query)] 

    #  if 'episodesNum' in type and query:
        #  outputs['episodesNum'] = gogoanimeEpisodesNum(query) 

    return outputs

if __name__ == "__main__":
    #  print(anilistInfo('episodesNum', query='boku'))

    #  result = vizerInfo('search', query='umbrella')
    #  print(result)
    #  searchresult = gogoanimeSearch('kimetsu')
    #  print(searchresult)
    #  epnumresult = gogoanimeEpisodesNum(searchresult[0][0])  
    #  print(epnumresult)
    #  epsresult = gogoanimeEpisodes(searchresult[0][0])  
    #  print(epsresult)


