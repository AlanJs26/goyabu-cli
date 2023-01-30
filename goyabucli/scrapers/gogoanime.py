from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers
from urllib.parse import quote
from parsel import Selector
from rich import print as rprint

from typing import List

import requests

class Gogoanime(Scraper):
    def __init__(self):
        super().__init__('gogoanime', ['en'])
        self._base_url = 'https://gogoanime.dk'
        self._api_info_url = 'https://api.consumet.org/anime/gogoanime/info'
        self._api_watch_url = 'https://api.consumet.org/anime/gogoanime/watch'

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
        gogo_ep_id = link.url.split('/')[-1]

        html = requests.get(f'{self._api_watch_url}/{gogo_ep_id}', headers=headers)
        json_result = html.json()

        if not json_result or not json_result['sources']:
            return []

        def parse_quality(quality:str):
            quality_map = {
                '144p': 'sd',
                '360p': 'sd',
                '480p': 'sd',
                '720p': 'hd',
                '1080p': 'full-hd',
            }
            if quality in quality_map:
                return quality_map[quality]

            return 'sd'

        links = []
        for stream_info in json_result['sources']:
            new_link = VideoUrl(
                url=stream_info['url'],
                quality=parse_quality(stream_info['quality']),
                lang='en',
                source=self.name
            ) 
            new_link.ready = True
            new_link.headers['Referer'] = json_result['headers']['Referer']
            links.append(new_link)

        link = links.pop(0)

        return links

    def search(self, query:str) -> List[Anime]:
        html = requests.get(f'{self._base_url}/search.html?keyword={quote(query)}', headers=headers).text
        dom = Selector(html)

        a = dom.xpath('//*[@id="wrapper_bg"]/section/section[1]/div/div[2]/ul/li/div/a')

        animes = []
        for item in a:
            animes.append(
                Anime(
                    item.attrib['title'],
                    animeTitle2Id(item.attrib['title']),
                    source=self.name,
                    pageUrl=item.attrib['href']
                )
            )

        return animes

    def episodes(self, animePageUrl) -> List[Episode]:

        gogo_anime_id = animePageUrl.split('/')[-1]

        html = requests.get(f'{self._api_info_url}/{gogo_anime_id}', headers=headers)
        json_result = html.json()

        if not json_result or not json_result['episodes']:
            return []

        episodes = []

        for ep in json_result['episodes']:
            new_ep = Episode(f'EP {ep["number"]}', str(ep['number']))
            new_ep.addSource(self.name, [VideoUrl(ep['url'], 'sd', 'en', self.name)])
            episodes.append(new_ep)
        episodes.sort(key=lambda x:x.id)

        return episodes

