from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers
from urllib.parse import quote_plus
from parsel import Selector

from typing import List

import requests
from lxml.html import fromstring

class Anime123(Scraper):
    def __init__(self):
        super().__init__('123anime', ['pt'])
        self._base_link = 'https://123anime.to'

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:

        def parse_quality(string:str):
            quality_map = {
                '144p': 'sd',
                '360p': 'sd',
                '480p': 'sd',
                '720p': 'hd',
                '1080p': 'full-hd',
            }

            for quality,real_quality in quality_map.items():
                if quality in string:
                    return real_quality

            return 'sd'


        html = requests.get(link.url, headers=headers).text
        dom = Selector(html)


        download_btn = dom.css('a.pc-download')
        if not download_btn:
            return []

        download_page = download_btn[0].attrib['href']
        print(download_page)

        html = requests.get(download_page, headers=headers).text
        dom = Selector(html)

        source_btns = dom.css('.mirror_link:first-of-type .dowload')
        print(source_btns)

        if not source_btns:
            return []

        link.url = source_btns[0].attrib['href']
        link.quality = parse_quality(source_btns[0].text)
        print(link.url)

        other_links = []
        for source_btn in source_btns[1:]:
            other_links.append(
                VideoUrl( source_btn.attrib['href'], parse_quality(source_btn.text), 'pt', self.name, ready=True)
            )

        return other_links

    def search(self, query:str) -> List[Anime]:

        html = requests.get(f'{self._base_link}/search?keyword={quote_plus(query)}', headers=headers).text
        dom = fromstring(html)

        imgs = dom.xpath('//*[@id="main-content"]/section/div[2]/div/div[1]/div/div[2]/h3/a')

        animes = []
        for item in imgs:
            animes.append(
                Anime(title=item.text,
                      id=animeTitle2Id(item.text),
                      source=self.name,
                      pageUrl=self._base_link+item.get('href')
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:

        html = requests.get(animePageUrl, headers=headers).text
        dom = fromstring(html)

        title = dom.xpath('//*[@id="ani_detail"]/div/div/div[2]/div[2]/h2')[0].text.strip()
        episodes_string = dom.xpath('//*[@id="ani_detail"]/div/div/div[2]/div[3]/div[1]/div[4]/span[2]')[0].text.replace(' ', '')

        if isinstance(episodes_string, str) and isinstance(title, str):
            available_episodes_string = episodes_string.split('/')[0]

            episodes = []
            for index in range(1,int(available_episodes_string)+1):
                ep = Episode(f'{title} ({index})', str(index))

                url = VideoUrl(f'{animePageUrl.replace("/anime/", "/watch/")}-episode-{index}','sd','pt',self.name)
                ep.addSource(self.name, [url])

                episodes.append(ep)
            return episodes
        else:
            raise Exception(f'Cannot fetch episodes from {animePageUrl}')
