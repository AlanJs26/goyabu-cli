from goyabucli.scraper import Scraper,Anime,Episode,VideoUrl
from goyabucli.utils import animeTitle2Id, headers

from typing import List

import requests
from lxml.html import fromstring
import re

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
        html = requests.get(f'https://goyabu.com/?s={query.replace(" ","+")}', headers=headers).text
        dom = fromstring(html)

        a_link = dom.xpath('//*[@id="main"]/div/div[1]/div/div/a')

        animes = []
        for item in a_link:
            animes.append(
                Anime(item.getnext().text,
                      animeTitle2Id(item.getnext().text),
                      source=self.name,
                      pageUrl=item.get('href')
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:
        html = requests.get(animePageUrl, headers=headers).text
        dom = fromstring(html)

        epnames = dom.xpath('//*[@id="main"]/div[1]/div/div[2]/div/div/a/div[2]')

        episodes = []
        for index,item in enumerate(epnames):
            ep = Episode(item.text, str(index+1))

            url = VideoUrl(item.getparent().get('href'),'sd','pt',self.name)
            ep.addSource(self.name, [url])

            episodes.append(ep)
        episodes.sort(key=lambda x:int(x.id), reverse=True)
        return episodes




