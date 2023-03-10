from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers
from urllib.parse import quote_plus

from typing import List

import requests
from parsel import Selector

class SuperAnimes(Scraper):
    def __init__(self):
        super().__init__('superanimes', ['pt'])

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
        html = requests.get(link.url, headers=headers).text
        dom = Selector(html)
        source_tag = dom.css('video>source') 

        if source_tag.attrib['src']:
            link.url = source_tag.attrib['src']
            link.ready = True
            link.headers['Referer'] = 'https://www.superanimes.biz/'

        return []



    def search(self, query:str) -> List[Anime]:

        html = requests.get(f'https://superanimes.biz/?s={quote_plus(query)}', headers=headers).text
        dom = Selector(html)

        links = dom.xpath('//*[@id="video_"]/a')

        animes = []
        for item in links:
            animes.append(
                Anime(item.attrib['title'],
                      animeTitle2Id(item.attrib['title']),
                      source=self.name,
                      pageUrl=item.attrib['href']
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:

        html = requests.get(animePageUrl, headers=headers).text
        dom = Selector(html)

        episodes = []
        index = 0

        next_btn = dom.css('.nextpostslink')
        while True:
            links = dom.xpath('//*[@id="telas"]/ul/li/div[2]/a')
            links_text = dom.xpath('//*[@id="telas"]/ul/li/div[2]/a/text()')

            for item, item_text in zip(links, links_text):
                index+=1

                ep = Episode(item_text.get(), str(index))

                url = VideoUrl(item.attrib['href'],'sd','pt',self.name)
                ep.addSource(self.name, [url])

                episodes.append(ep)

            if not next_btn:
                break
            html = requests.get(next_btn.attrib['href'], headers=headers).text
            dom = Selector(html)
            next_btn = dom.css('.nextpostslink')


        return episodes
