from typing import List
from scraper import Scraper,Anime,Episode,VideoUrl,bindScrapers
import requests
from bs4 import BeautifulSoup as bs4
from lxml import etree

from scraper import TScraper

class Goyabu(Scraper):
    def __init__(self):
        super().__init__('goyabu', ['pt'])
        self.scrapers

    @bindScrapers
    def search(self, query:str) -> List[Anime]:
        html = requests.get(f'https://goyabu.com/?s={query.replace(" ","+")}').text
        soup = bs4(html, 'html.parser')
        dom = etree.HTML(str(soup)).getroottree()

        a_link = dom.xpath('//*[@id="main"]/div/div[1]/div/div/a')

        animes = []
        for item in a_link:
            animes.append(
                Anime(item.getnext().text,
                      item.getnext().text,
                      source=self.name,
                      pageUrl=item.get('href')
                      )
            )
        return animes

    @bindScrapers
    def episodes(self, animePageUrl) -> List[Episode]:
        html = requests.get(animePageUrl).text
        soup = bs4(html, 'html.parser')
        dom = etree.HTML(str(soup)).getroottree()

        epnames = dom.xpath('//*[@id="main"]/div[1]/div/div[2]/div/div/a/div[2]')

        episodes = []
        index = 0
        for item in epnames:
            index+=1
            ep = Episode(item.text, str(index))

            url = VideoUrl(item.getparent().get('href'),'sd','pt',self.name)
            ep.addSource(self.name, [url])

            episodes.append(ep)
        return episodes




