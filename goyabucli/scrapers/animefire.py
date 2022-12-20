from ..scraper import Scraper,Anime,Episode,VideoUrl
from ..utils import animeTitle2Id, headers
from ..extractors.blogger import BloggerExtractor

from typing import List

import requests
from lxml.html import fromstring

class AnimeFire(Scraper):
    def __init__(self):
        super().__init__('animefire', ['pt'])

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
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

        video_api_url = link.url.replace('animes', 'video', 1)

        html = requests.get(video_api_url, headers=headers)
        json_result = html.json()

        if not json_result or not json_result['data']:
            link.ready = False
            return []


        if 'token' in json_result and 'blogger' in json_result['token']:
            foundStreams = [{'src': item, 'label': '360p'} for item in BloggerExtractor.parseUrl(json_result['token'])]
        else:
            foundStreams = json_result['data']


        link.url = foundStreams[0]['src']
        link.quality = parse_quality(foundStreams[0]['label'])

        link.ready = True

        other_links = []
        for item in foundStreams[1:]:
            other_links.append(
                VideoUrl( item['src'], parse_quality(item['label']), 'pt', self.name, ready=True)
            )

        return other_links

    def search(self, query:str) -> List[Anime]:

        html = requests.get(f'https://animefire.net/pesquisar/{query.replace(" ", "-")}', headers=headers).text
        dom = fromstring(html)

        imgs = dom.xpath('//*[@id="body-content"]/div[2]/div/div/div/div/article/a/div[1]/h3')

        animes = []
        for item in imgs:
            animes.append(
                Anime(item.text,
                      animeTitle2Id(item.text),
                      source=self.name,
                      pageUrl=item.getparent().getparent().get('href')
                      )
            )
        return animes

    def episodes(self, animePageUrl) -> List[Episode]:

        html = requests.get(animePageUrl, headers=headers).text
        dom = fromstring(html)

        epnames = dom.xpath('//*[@id="body-content"]/div[1]/div/div[2]/section/div[2]/a')

        episodes = []
        index = 0
        for item in epnames:
            index+=1
            ep = Episode(item.text, str(index))

            url = VideoUrl(item.get('href'),'sd','pt',self.name)
            ep.addSource(self.name, [url])

            episodes.append(ep)
        return episodes
