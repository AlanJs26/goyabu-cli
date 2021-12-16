from typing import Callable, Dict, List, Optional, Union, overload
from bs4 import BeautifulSoup as bs4
import requests
import re
from scrappers.utils import infoDecorator
#  from utils import infoDecorator
#  from rich import print

possibleOutputs = [
    'search',
    'episodes',
]



def vizerSearch(name:str) -> List[str]:
    html = requests.get(f'https://vizer.tv/pesquisar/{" ".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    animeList = soup.find(class_='listItems')
    namelist = [name.text for name in animeList.find_all('span')] 
    watchIdlist = [re.search(r'\/(.+?\/){4}(.+)\.jpg', link['src'])[2] for link in animeList.find_all('img')]

    return list(zip(namelist, watchIdlist)) 

def vizerMovie(watchId:str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"watchMovie": watchId}, headers=headers)
    idlanglist = r.json()['list']
    playid = "0"
    for index in idlanglist:
        playid = idlanglist[index]['id']
        if idlanglist[index]['lang'] == "Dublado":
            break


    #  playid = r.json()['list']["0"]['id']

    r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={playid}&sv=fembed", headers=headers)
    nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]
    newId = re.search(r'(?<=v\/).+?(?=#|$)', nexthref)[0]

    r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
    finalUrl = r.json()['data'][-1]['file']

    return finalUrl

def vizerMovieByName(name:str) -> Dict[str, str]: 
    results = vizerSearch(name)
    resultsFiltered = [result for result in results if result[0] == name]

    if len(resultsFiltered) == 0:
        chosenName = results[0][0]
        chosenWatchId = results[0][1]
    else:
        chosenName = resultsFiltered[0][0]
        chosenWatchId = resultsFiltered[0][1]

    return {chosenName: vizerMovie(chosenWatchId)}




@infoDecorator(possibleOutputs)
def vizerInfo(*type:str, query:Optional[str]=None) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'search' in type and query:
        outputs['search'] = [item[0] for item in vizerSearch(query)] 

    if 'episodes' in type and query:
        outputs['episodes'] = vizerMovieByName(query) 

    return outputs

if __name__ == "__main__":
    #  print(anilistInfo('episodesNum', query='boku'))

    result = vizerInfo('search', query='Venom')
    print(result)
    #  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    #  r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"watchMovie": 25659}, headers=headers)
    #  playid = r.json()['list']["0"]['id']

    #  r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={playid}&sv=fembed", headers=headers)
    #  nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]
    #  newId = re.search(r'(?<=v\/).+?(?=#)', nexthref)[0]

    #  r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
    #  finalUrl = r.json()['data'][-1]['file']

    # ,(\d+).\1,\'\|(.+?\|)mp4
