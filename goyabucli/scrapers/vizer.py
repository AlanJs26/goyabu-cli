from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers
from ..progress import progress
from urllib.parse import quote

from typing import List

import requests
from parsel import Selector
import re
import PyBypass as bypasser

class Vizer(Scraper):
    def __init__(self):
        super().__init__('vizer', ['pt'])

    def search(self, query:str) -> List[Anime]:

        html = requests.get(f'https://vizer.tv/pesquisar/{quote(query)}', headers=headers).text
        dom = Selector(html)

        links = dom.xpath('//*[@id="seriesList"]/div[3]/a')
        titles = dom.xpath('//*[@id="seriesList"]/div[3]/a/div/span/text()')

        animes = []
        for item,title in zip(links, titles):
            animes.append(
                Anime(title.get(),
                      animeTitle2Id(title.get()),
                      source=self.name,
                      pageUrl='https://vizer.tv/'+item.attrib['href']
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:

        html = requests.get(animePageUrl, headers=headers).text
        dom = Selector(html)

        wrap_for_series = dom.css('main>.wrap#lp')

        episodes:List[Episode] = []
        if wrap_for_series:

            seasons = dom.css('#seasonsList > .item')

            with progress(total=len(seasons), postfix='fetching seasons', leave=False) as pbar:
                for i,season in enumerate(seasons):
                    result = requests.post(
                        url='https://vizer.tv/includes/ajax/publicFunctions.php',
                        data={
                            'getEpisodes': int(season.attrib['data-season-id'])
                        },
                        headers=headers).json()

                    for item in result['list'].values():

                        episode = Episode(title=f'S{i+1}E{item["name"]} - {item["title"]}', id=str(len(episodes)+1))

                        result = requests.post(
                            url='https://vizer.tv/includes/ajax/publicFunctions.php',
                            data={
                                'getEpisodeLanguages': int(item['id'])
                            },
                            headers=headers).json()

                        for lang_item in result['list'].values():
                            lang = 'en' if lang_item['lang'] == '1' else 'pt'
                            url = VideoUrl(lang_item['id'],'sd',lang,self.name)
                            episode.addSource(self.name, [url])

                        episodes.append(episode)
                    pbar.update(1)

        return episodes


    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:

        availablePlayers = requests.post(
            'https://vizer.tv/includes/ajax/publicFunctions.php',
            data={
                'getVideoPlayers': link.url
            },
            headers=headers).json()

        if availablePlayers['streamtape'] == '0' and availablePlayers['fembed'] == '0':
            return []

        source = 'streamtape' if availablePlayers['streamtape'] != '0' else 'fembed'
        http = requests.get(f'https://vizer.tv/embed/getPlay.php?id={link.url}&sv={source}', headers=headers).text
        match = re.search(r'window\.location\.href=\"(.+?)\"', http)

        if not match:
            return []

        url = match.group(1)
        url = url.split('?')[0]
        bypassed_url = bypasser.bypass(url)

        if bypassed_url:
            link.url = bypassed_url
            link.ready = True
                

        return []

