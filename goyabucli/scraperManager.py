from typing import List, Dict
from .scraper import Scraper,Anime,bindScrapers
from .scrapers.goyabu import Goyabu
from .scrapers.animefire import AnimeFire
from .scrapers.gogoanime import Gogoanime
from .scrapers.superanimes import SuperAnimes
from .scrapers.vizer import Vizer
from .progress import ProgressBar
from rich import print as rprint

SCRAPERS:List[Scraper] = [AnimeFire(), Gogoanime(), SuperAnimes(), Goyabu(), Vizer()]

def get_scrapers_as_dict():
    return { scraper.name: scraper for scraper in SCRAPERS }

class ScraperManager():
    def __init__(self):
        self.scrapers = SCRAPERS

        self.animes:Dict[str,Anime] = {
            # 'id1' : Anime('title', 'anime1')
        }

    def test(self, verbose=False) -> dict[str,bool]:
        results = self.search('a', verbose=True)
        working_dict = {}
        for scraper in self.scrapers:
            sample_anime = None
            for anime in results:
                if scraper.name in anime.availableScrapers:
                    sample_anime=anime
                    break
            if sample_anime is None:
                working_dict[scraper.name] = False
                continue

            if verbose:
                rprint(f'testing "{scraper.name}" with "{sample_anime.title}"')

            episodes = sample_anime.retrieveEpisodes()
            if not episodes:
                working_dict[scraper.name] = False
                continue

            episodes[0].retrieveLinks(scraper.name)
            links = episodes[0].getLinksBySource(scraper.name)
            working_dict[scraper.name] = any(link.test(verbose=verbose) for link in links)

        return working_dict

    @bindScrapers
    def search(self, query:str, preferedScrapers=[], verbose=False) -> List[Anime]:
        scrapers = self.scrapers
        if preferedScrapers:
            scrapers = [scraper for scraper in self.scrapers if scraper.name in preferedScrapers]

        new_animes = []

        pbar = None
        if verbose:
            pbar = ProgressBar(total=len(scrapers), postfix=[scraper.name for scraper in self.scrapers], leave=False)

        for scraper in scrapers:
            try:
                search_result = scraper.search(query)
            except:
                print(f'Error searching {scraper.name}\r')
                if pbar:
                    pbar.update(1)
                continue

            for anime in search_result:
                if new_anime := self._addAnime(anime): 
                    new_animes.append(new_anime)
            if pbar:
                pbar.update(1)
        if pbar:
            pbar.close()

        return new_animes

    # def searchLocal(self, query:str) -> List[Anime]:
    #     return [Anime('title', 'anime1')]

    def _addAnime(self, new_anime:Anime) -> None|Anime:
        if new_anime.id in self.animes:
            self.animes[new_anime.id].merge(new_anime)
        else:
            self.animes[new_anime.id] = new_anime
            return new_anime

