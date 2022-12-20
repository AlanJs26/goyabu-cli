from typing import List,Tuple,Set,Dict

class VideoUrl():
    def __init__(self, url:str, quality:str, lang:str, source:str, scrapers:List['Scraper']=[], ready=False):
        self.scrapers = scrapers
        self.url = url
        self.source = source
        self.ready = ready
        self.lang = lang
        self.quality = quality # sd,hd,full-hd,ultra-hd

    def getLink(self) -> List['VideoUrl']:
        right_scraper = next((scraper for scraper in self.scrapers if scraper.name == self.source), None)

        if right_scraper == None:
            raise LookupError(f"Cannot find matching scraper for '{self.source}'")

        found_links = right_scraper.parseLink(self)

        return found_links


    def test(self) -> bool:
        return True

def bindScrapers(f):
    def wrapper(self, *args, **kwargs):
        result = f(self,*args,**kwargs)
        for item in result:
            item.scrapers = self.scrapers
        return result
    return wrapper


class Episode():
    def __init__(self, title:str, id:str, scrapers:List['Scraper']=[]):
        self.scrapers = scrapers
        self.id = id
        self.index = 0
        self.title = title
        self.sources : List[Tuple[str,List[VideoUrl]]] = [] # (source_name, [video_url,...])
        self.description = ''

    def getLinksBySource(self, sourceName:str) -> List[VideoUrl]:
        videoUrls = next((source[1] for source in self.sources if source[0] == sourceName),None)

        if not self.scrapers:
            raise LookupError(f"Cannot access scrapers in episode {self.title}")

        if videoUrls == None:
            raise LookupError(f"Cannot find matching source for '{sourceName}' in episode {self.title}")

        return videoUrls

    def retrieveLinks(self, scraperName:str):
        right_scraper = next((source[1] for source in self.sources if source[0] == scraperName),None)

        if not self.scrapers:
            raise LookupError(f"Cannot access scrapers in episode {self.title}")

        if right_scraper == None:
            raise LookupError(f"Cannot find matching source for '{scraperName}' in episode {self.title}")

        found_links = []
        for source in right_scraper:
            found_links.extend(source.getLink())

        right_scraper.extend(found_links)

        for source in right_scraper.copy():
            if not source.ready or not source.test():
                right_scraper.remove(source)




    def availableLanguages(self) -> List[str]:
        langs : Set[str] = set()

        for _,videourl_list in self.sources:
            for videourl in videourl_list:
                langs.add(videourl.lang)

        return list(langs)


    @bindScrapers
    def addSource(self, sourceName:str, urls:List[VideoUrl]) -> List[VideoUrl]:
        working_urls = list(filter(lambda x : x.test(), urls))

        # print(self.scrapers)
        if all(sourceName != source for source,_ in self.sources):
            self.sources.append((sourceName, working_urls))
            # print(working_urls[0].scrapers)
            return working_urls

        for item in self.sources:
            if item[0] == sourceName:
                filtered_urls : List[VideoUrl] = []
                for new_videourl in working_urls:
                    if all(new_videourl.url != videourl.url for videourl in item[1]):
                        filtered_urls.append(new_videourl)

                item[1].extend(filtered_urls)

        return next(videourls for source,videourls in self.sources if source == sourceName)

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
        self.episodes:Dict[str,Episode] = {
            # 'id1' : Episode('title', 'id1')
        }
        self.availableScrapers = [source]

        self.source = source
        self.pageUrl:Dict[str,str] = {
            source: pageUrl
        }

    def retrieveEpisodes(self) -> List[Episode]:
        right_scraper = next((scraper for scraper in self.scrapers if scraper.name == self.source), None)

        if right_scraper == None:
            raise LookupError(f"Cannot find matching scraper for '{self.source}'")

        for index,episode in enumerate(right_scraper.episodes(self.pageUrl[self.source])):
            episode.index = index
            self._addEpisode(episode)
            # self.episodes[episode.id] = episode

        return list(self.episodes.values())

    def _addEpisode(self, episode:Episode):
        # bind scrapers to nested videourls
        episode.scrapers = self.scrapers
        for source in episode.sources:
            for videourl in source[1]:
                videourl.scrapers = self.scrapers

        if episode.id in self.episodes:
            self.episodes[episode.id].merge(episode)
        else:
            self.episodes[episode.id] = episode
        pass

    def merge(self, new_anime:'Anime'):
        self.availableScrapers = list(set([*self.availableScrapers,*new_anime.availableScrapers]))
        self.pageUrl = {**self.pageUrl, **new_anime.pageUrl}

        for episode in new_anime.episodes.values():
            self._addEpisode(episode)

class Scraper():
    def __init__(self, name:str, lang:List[str], scrapers:List['Scraper']=[]):
        self.scrapers:List['Scraper']=scrapers
        self.name = name
        self.lang = lang

    def parseLink(self, link:VideoUrl) -> List[VideoUrl]:
        raise NotImplementedError(f"parseLink not implemented for '{self.name}'")

    def search(self, query:str) -> List[Anime]:
        raise NotImplementedError(f"search not implemented for '{self.name}'")
        # return [Anime('anime_title', 'anime1')]

    def episodes(self, animePageUrl) -> List[Episode]:
        raise NotImplementedError(f"episodes not implemented for '{self.name}'")
        # return [Episode('title','ep1')]





