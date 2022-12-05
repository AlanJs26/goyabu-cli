import os
from typing import Dict, List, Optional, Union
from difflib import SequenceMatcher
from bs4 import BeautifulSoup as bs4
import requests
import re
# from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import infoDecorator
#  from utils import infoDecorator


hreflist = []
namelist = []
videolist = []

possibleOutputs = [
    'search',
    'episodes',
    'episodesNum',
    'language',
    'category'
]

def animesonlineSearch(name:str) -> List[str]:
    html = requests.get(f'https://animesonline.org/?s={"+".join(name.split(" "))}').text
    soup = bs4(html, 'html.parser')

    global hreflist
    global namelist

    animeList = soup.find(class_='search-page')
    results = zip([link['href'] for link in animeList.select('.title a')], [name.text for name in animeList.find_all('div', class_='title')])
    results = sorted(results, key=lambda x: SequenceMatcher(None, name, x[1]).ratio(), reverse=True)

    hreflist, namelist = [[name for name, _    in results],
                          [href for _   , href in results]]
    
    return namelist


def animesonlineEpisodes(name:str, slicelist=None) -> Dict[str, str]:

    if slicelist == None or type(slicelist) != list or len(slicelist) > 2 or len(slicelist) == 0:
        slicelist = [None, None]
    elif len(slicelist) == 1:
        slicelist[0] = int(slicelist[0]) if slicelist[0].isdigit() else None
        slicelist.append(int(slicelist[0])+1 if slicelist else None)
    else:
        slicelist = [int(i) if i.isdigit() else None for i in slicelist]


    global videolist
    global hreflist
    global namelist

    if len(namelist) == 0 or name not in namelist:
        animesonlineSearch(name)
        matched = list(filter(lambda x:x==name, hreflist))
        href = matched[0] if len(matched) else hreflist[0]
    else:
        href = hreflist[namelist.index(name)]

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    eplist = soup.select_one('#seasons')

    # TODO - fix this
    ep_hreflist = [ep['href'] for ep in eplist.select('.episodiotitle a')][slice(*slicelist)]
    ep_namelist = [name.text for name in eplist.select('.episodiotitle a')][slice(*slicelist)]
    videolist = ['' for _ in range(len(ep_hreflist))]

    def getvideourl(href, i):
        s = requests.Session()

        res = s.get(href)
        link = re.findall(r'(?<=a target="_blank" rel="noopener noreferrer" href=").+?(?=")',
                          res.text,
                          flags=re.DOTALL|re.MULTILINE)[0]

        res = s.get(link)

        link = re.findall(r'(?<=link\.href = ").+?(?=")', res.text, flags=re.DOTALL|re.MULTILINE)[0]

        res = s.get(link)

        token = re.findall(r'(?<=iframe src=").+?(?=")', res.text, flags=re.DOTALL|re.MULTILINE)[0]
        token = '='.join(token.split('=')[1:])

        cookies = {
            'token': token
        }

        res = s.get("https://guiafinancas.net/campanha.php", cookies=cookies)


        link = re.findall(r'(?<=iframe src=").+?(?=")', res.text, flags=re.DOTALL|re.MULTILINE)[0]

        res = s.get(link)

        link = re.findall(r'(?<="file":").+?(?=")', res.text, flags=re.DOTALL|re.MULTILINE)[0]
        finallink = link.replace('\\/', '/')

        videolist[i] = finallink

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(getvideourl, href, i) for i,href in enumerate(ep_hreflist)]
    # with tqdm(total=len(ep_hreflist)) as pbar:
    #     #  for i,href in enumerate(ep_hreflist):
    #         #  getvideourl(href, i)
    #         #  pbar.update(1)
    #
    #     with ThreadPoolExecutor(max_workers=3) as executor:
    #         futures = [executor.submit(getvideourl, href, i) for i,href in enumerate(ep_hreflist)]
    #         for _ in as_completed(futures):
    #             pbar.update(1)

    return {name:link for name,link in zip(ep_namelist, videolist)}

def animesonlineEpisodesNum(name:str) -> int:
    global hreflist
    global namelist

    if len(namelist) == 0 or name not in namelist:
        animesonlineSearch(name)
        href = hreflist[0] if len(hreflist) else []
    else:
        href = hreflist[namelist.index(name)]

    if href == []: return 0

    html = requests.get(href).text
    soup = bs4(html, 'html.parser')

    return len([_ for _ in soup.select('#seasons .episodiotitle')])


@infoDecorator(possibleOutputs)
def animesonlineInfo(*type:str, query:Optional[str]=None, **kwargs) -> Union[Dict[str, Dict[str, str]], List[str]]:

    outputs = {}

    if 'episodes' in type and query:
        if 'range' in kwargs:
            outputs['episodes'] = animesonlineEpisodes(query, slicelist=kwargs['range'])
        else:
            outputs['episodes'] = animesonlineEpisodes(query)

    if 'episodesNum' in type and query:
        outputs['episodesNum'] = animesonlineEpisodesNum(query)

    if 'search' in type and query:
        outputs['search'] = animesonlineSearch(query)

    if 'language' in type:
        outputs['language'] = 'pt'

    if 'category' in type:
        outputs['category'] = 'anime'

    return outputs

if __name__ == "__main__":
    #  result = animesonlineInfo('episodes', query='yuukaku', range=['3'])
    #  result = animesonlineInfo('episodes', query='spy', range=['2'])
    result = animesonlineInfo('episodesNum', query='spy')
    print(result)
