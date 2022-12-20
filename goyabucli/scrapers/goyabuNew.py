from goyabucli.scraper import Scraper,Anime,Episode,VideoUrl
from goyabucli.utils import animeTitle2Id, headers

from typing import List

import requests
from bs4 import BeautifulSoup as bs4
from lxml import etree
import re

class Goyabu(Scraper):
    def __init__(self):
        super().__init__('goyabu', ['pt'])
        self.scrapers

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
        html=requests.get(link.url, headers=headers).text 

        allmatches = re.findall(r"(?<=src=').+kanra\.dev.+?(?=')", html)
        allmatches = list(filter(bool, allmatches))
        if not allmatches:
            return []

        return [VideoUrl(allmatches[0],'sd', 'pt', self.name)]

    def search(self, query:str) -> List[Anime]:
        html = requests.get(f'https://goyabu.com/?s={query.replace(" ","+")}').text
        soup = bs4(html, 'html.parser')
        dom = etree.HTML(str(soup)).getroottree()

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
        html = requests.get(animePageUrl).text
        soup = bs4(html, 'html.parser')
        dom = etree.HTML(str(soup)).getroottree()

        epnames = dom.xpath('//*[@id="main"]/div[1]/div/div[2]/div/div/a/div[2]')

        episodes = []
        index = len(epnames)+1
        for item in epnames:
            index-=1
            ep = Episode(item.text, str(index))

            url = VideoUrl(item.getparent().get('href'),'sd','pt',self.name)
            ep.addSource(self.name, [url])

            episodes.append(ep)
        return episodes




