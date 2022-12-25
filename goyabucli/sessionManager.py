from .scraper import Anime,Scraper
from typing import List,Union
from datetime import datetime, timezone
from os import path, makedirs
import json
from .utils import getTotalEpisodesCount
from .dropdown import interactiveTable,bcolors
from .translation import t
from .progress import ProgressBar
from concurrent.futures import ThreadPoolExecutor, as_completed


class SessionItem():
    def __init__(self, anime:Anime, date_utc:int, episodesInTotal:int, availableEpisodes:int, lastEpisode:int, lastSource:str, watchTime=0, duration=0):
        self.anime = anime

        self.date_utc = datetime.fromtimestamp(date_utc,timezone.utc)
        self.episodesInTotal = episodesInTotal
        self.availableEpisodes = availableEpisodes
        self.watchTime = watchTime
        self.lastEpisode = lastEpisode
        self.lastSource = lastSource
        self.duration = duration

    @property
    def id(self):
        return self.anime.id

    @property
    def title(self):
        return self.anime.title

    @property
    def status(self):
        if self.lastEpisode == self.availableEpisodes and self.lastEpisode < self.episodesInTotal:
            return 'insync'
        elif self.lastEpisode < self.episodesInTotal:
            return 'ongoing'
        else:
            return 'complete'


class SessionManager():
    def __init__(self, root='', scrapers:List[Scraper]=[]):
        self.filename = '.lastsession.json'
        self.scrapers = scrapers

        if root != '':
            self.root = root
        else:
            self.root = path.dirname(__file__)

        if not path.isdir(root):
            makedirs(root, exist_ok=True)

        if not path.isfile(path.join(root,self.filename)):
            with open(path.join(root,self.filename), 'w') as file:
                json.dump({}, file)

        self.session_items = []
        self.session_items = self.load()

    def find(self, anime:Anime) -> Union[SessionItem,None]:
        found_anime = next((item for item in self.session_items if item.anime.id == anime.id), None)

        return found_anime

    def add(self, animes:List[Anime]):
        all_ids = [item.id for item in self.session_items]
        for anime in animes:
            if anime.id in all_ids: 
                right_sessionItem = self.session_items[all_ids.index(anime.id)]
                right_sessionItem.lastSource = anime.source
                right_sessionItem.availableEpisodes = len(anime.episodes)
                right_sessionItem.anime = anime

                # Move session item to the end of the list
                self.session_items.remove(right_sessionItem)
                self.session_items.append(right_sessionItem)
            else:
                self.session_items.append(
                    SessionItem(
                        anime,
                        int(datetime.now().timestamp()),
                        0,
                        len(anime.episodes),
                        0,
                        anime.source
                    )
                )

    def update(self, anime:Anime, lastEpisode:int, watchTime=0, duration=0):
        right_sessionItem = next(item for item in self.session_items if item.id == anime.id)

        if not right_sessionItem:
            raise IndexError(f"Cannot find '{anime.title}' in session items")

        right_sessionItem.lastEpisode = lastEpisode
        right_sessionItem.watchTime = watchTime
        right_sessionItem.duration = duration

    def remove(self, id:str):
        right_sessionItem = next(item for item in self.session_items if item.id == id)
        self.session_items.remove(right_sessionItem)

    def load(self) -> List[SessionItem]:
        with open(path.join(self.root,self.filename)) as file:
            self.content = content = json.load(file)

        session_items = []

        for id,json_anime in content.items():
            anime = Anime(json_anime['title'], id, source=json_anime['lastSource'])
            anime.pageUrl = json_anime['pageUrl']
            anime.scrapers = self.scrapers

            session_items.append(SessionItem(
                anime,
                json_anime['utc'],
                json_anime['episodesInTotal'],
                json_anime['availableEpisodes'],
                json_anime['lastEpisode'],
                json_anime['lastSource'],
                watchTime=json_anime['watchTime'],
                duration=json_anime['duration'],
            ))
        
        return session_items

    def dump(self, verbose=False, number_to_update=0):
        content = {}

        def updateSessionItem(i, session_item):
            availableEpisodes = session_item.availableEpisodes
            if number_to_update and i+1>len(self.session_items)-number_to_update:
                availableEpisodes = len(session_item.anime.retrieveEpisodes())

            content[session_item.id] = {
                'title': session_item.title,
                'pageUrl': session_item.anime.pageUrl,
                'utc': int(session_item.date_utc.timestamp()),
                'episodesInTotal': getTotalEpisodesCount(session_item.title) or availableEpisodes,
                'availableEpisodes': availableEpisodes,
                'lastEpisode': session_item.lastEpisode,
                'lastSource': session_item.lastSource,
                'watchTime': session_item.watchTime,
                'duration': session_item.duration
            }

        pbar = None
        if verbose:
            pbar = ProgressBar(total=len(self.session_items), postfix=t('Animes atualizados'), leave=False)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(updateSessionItem,i, session_item) for i,session_item in enumerate(self.session_items)]
            for _ in as_completed(futures):
                if pbar:
                    pbar.update(1)

        if pbar:
            pbar.close()

        with open(path.join(self.root,self.filename), 'w') as file:
            json.dump(content, file)

    def select(self, hintText=t('Digite: '), maxListSize=5, width=100, query='') -> Union[SessionItem,str]:

        if query:
            if query.isdigit():
                return self.session_items[len(self.session_items)-int(query)]
            return query

        def format_status(session_item:SessionItem) -> str:
            status = t("Episodio {} [{}/{}]", session_item.lastEpisode, session_item.availableEpisodes, session_item.episodesInTotal)

            if session_item.status == 'complete':
                status = bcolors['green']+t("Completo")+bcolors['end']
            elif session_item.status == 'insync':
                status = bcolors['grey']+status+bcolors['end']

            return status

        if not self.session_items:
            return str(input(hintText))

        table_rows = [[str(len(self.session_items)-index),item.title, format_status(item)] for index,item in enumerate(self.session_items)]


        results = interactiveTable(
            table_rows,
            ['' ,t("Sessoes anteriores"), t("Status")],
            "ccc",
            behaviour='multiSelectWithText',
            maxListSize=maxListSize,
            width=width,
            flexColumn=1,
            highlightRange=(2,2),
            hintText=hintText
        )

        
        if results.text:
            if results.text.isdigit():
                return self.session_items[len(self.session_items)-int(results['text'])]
            return results.text

        if results.selectedPos is None:
            raise Exception('Invalid position')

        return self.session_items[results.selectedPos]






