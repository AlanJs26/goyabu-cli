from typing import Dict, List, Optional, Tuple, Union, Tuple
from bs4 import BeautifulSoup as bs4
import requests
import re
from time import sleep
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import loads as load_json

from scrappers.utils import infoDecorator
#  from utils import infoDecorator

#  from rich import print

possibleOutputs = [
    'search',
    'episodes',
    'episodesNum',
]


wasBlocked = {}
count = 0

def vizerSearch(name:str) -> List[Tuple[str,str,bool]]:
    html = requests.get(f'https://vizer.tv/pesquisar/{" ".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    animeList = soup.find(class_='listItems')
    if not animeList or len(animeList) == 0:
        return []

    urllist:List[str] = [f'https://vizer.tv/{url["href"]}' for url in animeList.select('.gPoster')] 
    namelist:List[str] = [name.text for name in animeList.find_all('span')] 
    #  watchIdlist:List[str] = [re.search(r'\/(.+?\/){4}(.+)\.jpg', link['src'])[2] for link in animeList.find_all('img')]

    infos = animeList.find_all('div', class_='infos')
    isMovie:List[bool] = []
    for info in infos:
        c = info.select_one('.c, .t')

        isMovie.append(False if len(c.text) else True)
        #  isMovie.append(True)

    return list(zip(namelist, urllist, isMovie)) 

def vizerEpisodesNum(name:str) -> int:

    results = vizerSearch(name)
    resultsFiltered = [result for result in results if result[0] == name]

    if len(resultsFiltered):
        #  chosenWatchId = resultsFiltered[0][1]
        chosenIsMovie = resultsFiltered[0][2]
        movie_url = resultsFiltered[0][1]
    elif len(results):
        #  chosenWatchId = results[0][1]
        chosenIsMovie = results[0][2]
        movie_url = results[0][1]
    else:
        return 1

    if chosenIsMovie == True: 
        return 1


    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}

    #  r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getSeasons": chosenWatchId}, headers=headers)
    #  rawResult = r.json()['list']
    #  seasons = []
    #  for index in rawResult:
        #  newItem = (rawResult[index]['id'], rawResult[index]['name'])
        #  seasons.append(newItem)

    html = requests.get(movie_url).text
    soup = bs4(html, 'html.parser')
    season_items = soup.select('.bslider .item')
    seasons = [(item['data-season-id'], item.text) for item in season_items]

    episodescount = 0
    for season in seasons:
        seasonId, _ = season

        r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getEpisodes": seasonId}, headers=headers)
        rawResult = r.json()['list']
        episodescount+= len(rawResult)

    return episodescount

def vizerMovie(movie_url:str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    html = requests.get(movie_url).text

    raw_langs = re.search(r'(?<=videoPlayerBox\(){"status.+(?=\);)', html)[0]

    langs_id = [item['id'] for item in load_json(raw_langs)['list'].values()]

    chosen_lang_id = langs_id[-1]


    r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={chosen_lang_id}&sv=fembed", headers=headers)

    nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]

    r = requests.get(url=nexthref)

    api_url = re.search('https?://.+?(?=/)', r.url)[0]
    fembed_id = nexthref.split('/')[-1]

    r = requests.post(url=f'{api_url}/api/source/{fembed_id}')

    finalUrl = r.json()['data'][-1]['file']

    return finalUrl



def vizerSeries(movie_url:str, slicelist=None) -> Dict[str, str]:

    if slicelist == None or type(slicelist) != list or len(slicelist) != 2:
        slicelist = [None, None]
    else:
        slicelist = [int(i) if i.isdigit() else None for i in slicelist]
        slicelist[1] = slicelist[1] and slicelist[1]+1

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}

    html = requests.get(movie_url).text
    soup = bs4(html, 'html.parser')
    season_items = soup.select('.bslider .item')
    seasons = [(item['data-season-id'], item.text) for item in season_items]


    #  r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getSeasons": watchId}, headers=headers)

    #  rawResult = r.json()['list']
    #  seasons = []
    #  for index in rawResult:
        #  newItem = (rawResult[index]['id'], rawResult[index]['name'])
        #  seasons.append(newItem)

    episodesBySeason = []
    for season in seasons:
        seasonId, seasonName = season

        r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getEpisodes": seasonId}, headers=headers)
        rawResult = r.json()['list']
        for index in rawResult:
            episodesBySeason.append((rawResult[index]['id'], f"S{seasonName} - {rawResult[index]['title']}"))

    episodesBySeason = episodesBySeason[slice(*slicelist)]



    #  playid = r.json()['list']["0"]['id']
    finalUrls: List[Union[Tuple[str, str], str]] = ['' for _ in episodesBySeason]
    
    def getvideourl(episode, index):
        global wasBlocked
        global count

        episodeId, episodeName = episode

        okcount = 0

        while True:
            while any(wasBlocked.values()):
                print(index)
                sleep(2)

            count += 1
            sleep(count)

            if count > 5:
                count = 0
                wasBlocked[index] = True
                sleep(5)
                wasBlocked[index] = False

            r = ''
            try:
                r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"getEpisodeLanguages": episodeId}, headers=headers)
                languages = [(item['id'], item['lang']) for item in r.json()['list'].values()] 

                r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={languages[-1][0]}&sv=fembed", headers=headers)
                nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]

                r = requests.get(url=nexthref)
                api_url = re.search('https?://.+?(?=/)', r.url)[0]
                fembed_id = nexthref.split('/')[-1]

                r = requests.post(url=f'{api_url}/api/source/{fembed_id}')

                finalUrls[index] = (episodeName, r.json()['data'][-1]['file'])

                break
            except Exception:
                print(f'{r.reason} - {index}')
                if 'Many' in r.reason:
                    wasBlocked[index] = True
                    sleep(5)
                    wasBlocked[index] = False
                elif 'OK' in r.reason:
                    okcount+=1
                    if okcount >=5:
                        finalUrls[index] = (episodeName, 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4')
                        break


    with tqdm(total=len(episodesBySeason)) as pbar:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(getvideourl, episode, index) for index, episode in enumerate(episodesBySeason)]
            for _ in as_completed(futures):
                pbar.update(1)

    #  print(finalUrls)

    return {name:link for name,link in finalUrls}

def vizerEpisodes(name:str, slicelist=None) -> Dict[str, str]: 

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
        return vizerSeries(chosenWatchId, slicelist=slicelist)




@infoDecorator(possibleOutputs)
def vizerInfo(*type:str, query:Optional[str]=None, **kwargs) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'search' in type and query:
        outputs['search'] = [item[0] for item in vizerSearch(query)] 

    if 'episodesNum' in type and query:
        outputs['episodesNum'] = vizerEpisodesNum(query)

    if 'episodes' in type and query:
        if 'range' in kwargs:
            outputs['episodes'] = vizerEpisodes(query, slicelist=kwargs['range']) 
        else:
            outputs['episodes'] = vizerEpisodes(query) 

    return outputs

if __name__ == "__main__":
    #  print(anilistInfo('episodesNum', query='boku'))

    result = vizerSearch('aranha')
    print(result)
    #  vizersearchresult = vizerSearch('umbrella')
    #  print(vizersearchresult)

    #  vizerseriesresult = vizerSeries('5263')
    #  print(vizerseriesresult)
    #  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    #  r = requests.post(url="https://vizer.tv/includes/ajax/publicFunctions.php", data={"watchMovie": 25659}, headers=headers)
    #  playid = r.json()['list']["0"]['id']

    #  r = requests.get(url=f"https://vizer.tv/embed/getPlay.php?id={playid}&sv=fembed", headers=headers)
    #  nexthref = re.search(r'(?<=window\.location\.href=\").+?(?=\";)', r.text)[0]
    #  newId = re.search(r'(?<=v\/).+?(?=#)', nexthref)[0]

    #  r = requests.post(url=f"https://diasfem.com/api/source/{newId}")
    #  finalUrl = r.json()['data'][-1]['file']

    # ,(\d+).\1,\'\|(.+?\|)mp4
