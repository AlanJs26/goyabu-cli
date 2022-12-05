from typing import List
from scraper import Scraper,Anime,bindScrapers
# from scrapersversiontwo.goyabuNew import Goyabu
from scrapersversiontwo.animefire import AnimeFire

SCRAPERS:List[Scraper] = [AnimeFire()]


class ScraperManager():
    def __init__(self):
        self.scrapers = SCRAPERS
        self.animes = {
            # 'id1' : Anime('title', 'anime1')
        }

    @bindScrapers
    def search(self, query:str) -> List[Anime]:
        animes = []
        for scraper in self.scrapers:
            for anime in scraper.search(query):
                animes.append(anime)
                self._addAnime(anime)

        return animes

    def searchLocal(self, query:str) -> List[Anime]:
        return [Anime('title', 'anime1')]

    def _addAnime(self, new_anime:Anime):
        if new_anime.id in self.animes:
            self.animes[new_anime.id].merge(new_anime)
        else:
            self.animes[new_anime.id] = new_anime
