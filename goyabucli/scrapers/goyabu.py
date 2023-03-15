from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers

from typing import List

import requests
import re
from parsel import Selector

class Goyabu(Scraper):
    def __init__(self):
        super().__init__('goyabu', ['pt'])

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
        html=requests.get(link.url, headers=headers).text 

        allmatches = re.findall(r"soishi = '(.+?)'", html)
        allmatches = list(filter(bool, allmatches))
        if not allmatches:
            return []
        videotoken = allmatches[0]

        html=requests.get('https://kanra.dev/sashiki.php?claire='+videotoken, headers=headers)
        content = html.json()

        link.url = content['high'] or ''
        link.quality = 'hd'
        link.ready = bool(link.url)

        if content['low']:
            return [VideoUrl( content['low'], 'sd', self.lang[0], self.name, ready=True)]

        return []

    def search(self, query:str) -> List[Anime]:
        html = requests.get(f'https://goyabu.org/?s={query.replace(" ","+")}', headers=headers).text
        dom = Selector(html)

        a_link = dom.xpath('//*[@id="main"]/div/div[1]/div/div')

        animes = []
        for item in a_link:
            a = item.css('a')[0]
            h3 = item.xpath('h3/text()')[0]

            animes.append(
                Anime(h3.get(),
                      animeTitle2Id(h3.get()),
                      source=self.name,
                      pageUrl=a.attrib['href']
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:
        html = requests.get(animePageUrl, headers=headers).text
        dom = Selector(html)

        epnames = dom.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/div/div/div[@class="anime-episode"]')

        episodes = []
        for index,item in enumerate(epnames):
            a = item.css('a')[0]
            h3 = item.xpath('h3/text()')[0]

            ep = Episode(h3.get(), str(len(epnames)-index))

            url = VideoUrl(a.attrib['href'],'sd','pt',self.name)
            ep.addSource(self.name, [url])

            episodes.append(ep)
        episodes.sort(key=lambda x:int(x.id), reverse=False)
        return episodes




