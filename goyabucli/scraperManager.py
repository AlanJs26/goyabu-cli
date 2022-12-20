from typing import List, Dict
from .scraper import Scraper,Anime,bindScrapers
from .scrapers.goyabuNew import Goyabu
from .scrapers.animefire import AnimeFire

SCRAPERS:List[Scraper] = [AnimeFire(), Goyabu()]

class ScraperManager():
    def __init__(self):
        self.scrapers = SCRAPERS
        self.animes:Dict[str,Anime] = {
            # 'id1' : Anime('title', 'anime1')
        }

    @bindScrapers
    def search(self, query:str, preferedScrapers=[]) -> List[Anime]:
        scrapers = self.scrapers
        if preferedScrapers:
            scrapers = [scraper for scraper in self.scrapers if scraper.name in preferedScrapers]

        for scraper in scrapers:
            for anime in scraper.search(query):
                self._addAnime(anime)

        return list(self.animes.values())

    def searchLocal(self, query:str) -> List[Anime]:
        return [Anime('title', 'anime1')]

    def _addAnime(self, new_anime:Anime):
        if new_anime.id in self.animes:
            self.animes[new_anime.id].merge(new_anime)
        else:
            self.animes[new_anime.id] = new_anime
