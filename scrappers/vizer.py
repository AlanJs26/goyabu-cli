from typing import Callable, Dict, List, Optional, Tuple, Union, overload
from bs4 import BeautifulSoup as bs4
import requests
import re
from time import sleep
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrappers.utils import infoDecorator
#  from utils import infoDecorator

#  from rich import print

possibleOutputs = [
    'search',
    'episodes',
]


wasBlocked = False

def vizerSearch(name:str) -> List[str]:
    html = requests.get(f'https://vizer.tv/pesquisar/{" ".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    animeList = soup.find(class_='listItems')
    namelist = [name.text for name in animeList.find_all('span')] 
    watchIdlist = [re.search(r'\/(.+?\/){4}(.+)\.jpg', link['src'])[2] for link in animeList.find_all('img')]
    infos = animeList.find_all('div', class_='infos')
    isMovie = []
    for info in infos:
        c = info.find_all('div', class_='c')
        isMovie.append(False if len(c) else True)

    return list(zip(namelist, watchIdlist, isMovie)) 

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
    print(nexthref)
    newId = re.search(r'(?<=v\/).+?(?=#|$)', nexthref)[0]

    r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
    finalUrl = r.json()['data'][-1]['file']

    return finalUrl


def vizerSeries(watchId:str) -> Dict[str, str]:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getSeasons": watchId}, headers=headers)
    rawResult = r.json()['list']
    seasons = []
    for index in rawResult:
        newItem = (rawResult[index]['id'], rawResult[index]['name'])
        seasons.append(newItem)

    episodesBySeason = []
    for season in seasons:
        seasonId, seasonName = season

        r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getEpisodes": seasonId}, headers=headers)
        rawResult = r.json()['list']
        for index in rawResult:
            episodesBySeason.append((rawResult[index]['id'], f"S{seasonName} - {rawResult[index]['title']}"))



    #  playid = r.json()['list']["0"]['id']
    finalUrls: List[Union[Tuple[str, str], str]] = ['' for _ in episodesBySeason]
    
    def getvideourl(episode, index):
        global wasBlocked

        while True:
            while wasBlocked == True:
                sleep(5)

            try:
                episodeId, episodeName = episode

                r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getEpisodeLanguages": episodeId}, headers=headers)
                languages = [(item['id'], item['lang']) for item in r.json()['list'].values()] 


                r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={languages[-1][0]}&sv=fembed", headers=headers)
                #  print(r.text)
                nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]
                newId = re.search(r'(?<=v\/).+?(?=#|$)', nexthref)[0]

                r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
                finalUrls[index] = (episodeName, r.json()['data'][-1]['file'])
                break
            except Exception:
                print('blocked')
                wasBlocked = True
                sleep(2)
                wasBlocked = False


    with tqdm(total=len(episodesBySeason)) as pbar:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(getvideourl, episode, index) for index, episode in enumerate(episodesBySeason)]
            for _ in as_completed(futures):
                pbar.update(1)

    #  print(finalUrls)

    return {name:link for name,link in finalUrls}

def vizerEpisodes(name:str) -> Dict[str, str]: 
    results = vizerSearch(name)
    resultsFiltered = [result for result in results if result[0] == name]

    if len(resultsFiltered) == 0:
        chosenName = results[0][0]
        chosenWatchId = results[0][1]
        chosenIsMovie = results[0][2]
    else:
        chosenName = resultsFiltered[0][0]
        chosenWatchId = resultsFiltered[0][1]
        chosenIsMovie = resultsFiltered[0][2]

    if chosenIsMovie == True: 
        return {chosenName: vizerMovie(chosenWatchId)}
    else:
        return vizerSeries(chosenWatchId)




@infoDecorator(possibleOutputs)
def vizerInfo(*type:str, query:Optional[str]=None) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'search' in type and query:
        outputs['search'] = [item[0] for item in vizerSearch(query)] 

    if 'episodes' in type and query:
        outputs['episodes'] = vizerEpisodes(query) 

    return outputs

if __name__ == "__main__":
    #  print(anilistInfo('episodesNum', query='boku'))

    #  result = vizerInfo('search', query='umbrella')
    #  print(result)
    #  vizersearchresult = vizerSearch('umbrella')
    #  print(vizersearchresult)

    vizerseriesresult = vizerSeries('5263')
    print(vizerseriesresult)
    #  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    #  r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"watchMovie": 25659}, headers=headers)
    #  playid = r.json()['list']["0"]['id']

    #  r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={playid}&sv=fembed", headers=headers)
    #  nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]
    #  newId = re.search(r'(?<=v\/).+?(?=#)', nexthref)[0]

    #  r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
    #  finalUrl = r.json()['data'][-1]['file']

    # ,(\d+).\1,\'\|(.+?\|)mp4
