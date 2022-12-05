from scraper import Anime,Scraper
from typing import List,Union
from datetime import timezone
from datetime import datetime
from os import path
import json
from utils import getTotalEpisodesCount
from dropdown import interactiveTable,bcolors

class SessionItem():
    def __init__(self, anime:Anime, date_utc:int, episodesInTotal:int, availableEpisodes:int, lastEpisode:int, lastSource:str):
        self.anime = anime

        self.date_utc = datetime.fromtimestamp(date_utc,timezone.utc)
        self.episodesInTotal = episodesInTotal
        self.availableEpisodes = availableEpisodes
        self.watchTime = 0
        self.lastEpisode = lastEpisode
        self.lastSource = lastSource

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

        if not path.isfile(path.join(root,self.filename)):
            with open(path.join(root,self.filename), 'w') as file:
                json.dump({}, file)

        self.session_items = []
        self.session_items = self.load()

    def add(self, animes:List[Anime]):
        all_ids = [item.id for item in self.session_items]
        for anime in animes:
            if anime.id in all_ids: 
                right_sessionItem = self.session_items[all_ids.index(anime.id)]
                right_sessionItem.lastSource = anime.source
                right_sessionItem.availableEpisodes = len(anime.episodes)
                right_sessionItem.anime = anime
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

    def update(self, anime:Anime, lastEpisode:int, watchTime=0):
        right_sessionItem = next(item for item in self.session_items if item.id == anime.id)

        if not right_sessionItem:
            raise IndexError(f"Cannot find '{anime.title}' in session items")

        right_sessionItem.lastEpisode = lastEpisode
        right_sessionItem.watchTime = watchTime

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
            ))
        
        return session_items

    def dump(self):
        content = {}

        for session_item in self.session_items:
            content[session_item.id] = {
                'title': session_item.title,
                'pageUrl': session_item.anime.pageUrl,
                'utc': int(session_item.date_utc.timestamp()),
                'episodesInTotal': getTotalEpisodesCount(session_item.title),
                'availableEpisodes': session_item.availableEpisodes,
                'lastEpisode': session_item.lastEpisode,
                'lastSource': session_item.lastSource,
                'watchTime': session_item.watchTime
            }

        with open(path.join(self.root,self.filename), 'w') as file:
            json.dump(content, file)

    def select(self, hintText='Digite: ', maxListSize=5, width=0, flexColumn=0) -> Union[SessionItem,str]:

        def format_status(session_item:SessionItem) -> str:
            status = f"Episodio {session_item.lastEpisode} [{session_item.availableEpisodes}/{session_item.episodesInTotal}]"

            if session_item.status == 'complete':
                status = bcolors['green']+"Completo"+bcolors['end']
            elif session_item.status == 'insync':
                status = bcolors['grey']+status+bcolors['end']

            return status

        if not self.session_items:
            return str(input(hintText))

        table_rows = [[str(len(self.session_items)-index),item.title, format_status(item)] for index,item in enumerate(self.session_items)]


        results = interactiveTable(
            table_rows,
            ['' ,"Sessoes anteriores", "Status"],
            "ccc",
            behaviour='multiSelectWithText',
            maxListSize=maxListSize,
            width=width,
            flexColumn=flexColumn,
            highlightRange=(2,2),
            hintText=hintText
        )

        if results['text']:
            if results['text'].isdigit():
                return self.session_items[len(self.session_items)-int(results['text'])]
            return results['text']

        if results['selectedPos'] is None:
            raise Exception('Invalid position')

        return self.session_items[results['selectedPos']]






