from typing import List,Tuple,Set

class VideoUrl():
    def __init__(self, url, quality, lang, source, scrapers:List['Scraper']=[]):
        self.scrapers = scrapers
        self.url = url
        self.source = source
        self.ready = False
        self.lang = lang
        self.quality = quality # sd,hd,full-hd,ultra-hd

    def getLink(self):
        right_scraper = next((scraper for scraper in self.scrapers if scraper.name == self.source), None)

        if right_scraper == None:
            raise LookupError(f"Cannot find matching scraper for '{self.source}'")


        self.ready = True
        return right_scraper.parseLink(self.url)


    def test(self) -> bool:
        return True

class Episode():
    def __init__(self, title:str, id:str, scrapers:List['Scraper']=[]):
        self.scrapers = scrapers
        self.id = id
        self.title = title
        self.sources : List[Tuple[str,List[VideoUrl]]] = [] # (source_name, [video_url,...])
        self.description = ''

    def getSources(self) -> List[Tuple[str,List[VideoUrl]]]:
        return [('source1', [VideoUrl('link1', 'sd', 'portuguese', 'source1')])]

    def getLinks(self, sourceName:str):
        right_source = next((source[1] for source in self.sources if source[0] == sourceName),None)

        if not self.scrapers:
            raise LookupError(f"Cannot access scrapers in episode {self.title}")

        if right_source == None:
            raise LookupError(f"Cannot find matching source for '{sourceName}' in episode {self.title}")

        for source in right_source:
            yield source.getLink()

    def availableLanguages(self) -> List[str]:
        langs : Set[str] = set()

        for _,videourl_list in self.sources:
            for videourl in videourl_list:
                langs.add(videourl.lang)

        return list(langs)


    def addSource(self, sourceName:str, urls:List[VideoUrl]):
        working_urls = list(filter(lambda x : x.test(), urls))

        if all(sourceName != source for source,_ in self.sources):
            self.sources.append((sourceName, working_urls))
            return

        for item in self.sources:
            if item[0] == sourceName:
                filtered_urls : List[VideoUrl] = []
                for new_videourl in working_urls:
                    if all(new_videourl.url != videourl.url for videourl in item[1]):
                        filtered_urls.append(new_videourl)

                item[1].extend(filtered_urls)

    def merge(self, episode:'Episode', unsafe=False):
        if not unsafe and episode.id != self.id:
            return

        for source in episode.sources:
            self.addSource(source[0], source[1])


class Anime():
    def __init__(self, title:str, id:str, source='', pageUrl='', scrapers:List['Scraper']=[]):
        self.scrapers=scrapers
        self.id = id
        self.title = title
        self.episodes = {
            'id1' : Episode('title', 'id1')
        }
        self.source = source
        self.pageUrl = pageUrl

    def retrieveEpisodes(self):
        right_scraper = next((scraper for scraper in self.scrapers if scraper.name == self.source), None)

        if right_scraper == None:
            raise LookupError(f"Cannot find matching scraper for '{self.source}'")

        for episode in right_scraper.episodes(self.pageUrl):
            self.episodes[episode.id] = episode

    def _addEpisode(self, episode:Episode):
        if episode.id in self.episodes:
            self.episodes[episode.id].merge(episode)
        else:
            self.episodes[episode.id] = episode
        pass

    def merge(self, new_anime:'Anime'):
        for episode in new_anime.episodes.values():
            self._addEpisode(episode)

def bindScrapers(f):
    def wrapper(self, *args, **kwargs):
        result = f(self,*args,**kwargs)
        for item in result:
            item.scrapers = self.scrapers
        return result
    return wrapper

class Scraper():
    def __init__(self, name:str, lang:List[str], scrapers:List['Scraper']=[]):
        self.scrapers:List['Scraper']=scrapers
        self.name = name
        self.lang = lang

    def parseLink(self, url:str) -> str:
        raise NotImplementedError(f"parseLink not implemented for {self.name}")

    def search(self, query:str) -> List[Anime]:
        return [Anime('anime_title', 'anime1')]

    @bindScrapers
    def episodes(self, animePageUrl) -> List[Episode]:
        return [Episode('title','ep1')]





