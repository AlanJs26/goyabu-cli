from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import List
import webbrowser

from goyabucli.translation import error
from .scraper import Anime, Scraper
from .sessionManager import SessionItem, SessionManager
from .progress import ProgressBar, progress



class MissingToken(Exception):
    "Raised when AnilistManager doesn't have a token"
    pass

class MissingUsername(Exception):
    "Raised when AnilistManager doesn't have the username"
    pass

class AnimeNotFound(Exception):
    "Raised when AnilistManager can't find the requested anime in anilist"
    pass

class AnilistManager():
    def __init__(self, username:str, token='', scrapers:List[Scraper]=[], silent=False):
        self.username = username
        self.token = token
        self.silent = silent
        self.scrapers = scrapers

        self._client_id = '10523'

    def search(self, name:str) -> SessionItem:
        variables = {
            'name': name
        }
        query = '''
        query ($name: String) {
            Media(search: $name, type: ANIME) {
                id
                title {
                  romaji
                }
                episodes
                nextAiringEpisode {
                    episode
                }
            }  
        }
        '''
        result = self._request(query, variables)
        if 'errors' in result:
            raise AnimeNotFound()

        media = result['data']['Media']

        return SessionItem(
            Anime(media['title']['romaji'], media['title']['romaji']),
            media['episodes'],
            media['nextAiringEpisode']['episode'] if media['nextAiringEpisode'] else media['episodes'],
            1,
            '',
            anilist_id=media['id']
        )

    def search_by_id(self, id:int) -> SessionItem:
        variables = {
            'id': id
        }
        query = '''
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                  romaji
                }
                episodes
                nextAiringEpisode {
                    episode
                }
            }  
        }
        '''
        result = self._request(query, variables)
        if 'errors' in result:
            raise AnimeNotFound()

        media = result['data']['Media']

        return SessionItem(
            Anime(media['title']['romaji'], media['title']['romaji']),
            media['episodes'],
            media['nextAiringEpisode']['episode'] if media['nextAiringEpisode'] else media['episodes'],
            1,
            ''
        )

    def getTotalEpisodesCount(self, title=None, id=None):
        try:
            if id:
                return self.search_by_id(id).episodesInTotal
            elif title:
                return self.search(title).episodesInTotal
        except AnimeNotFound:
            return 0

        return 0

    def update_session(self, session:SessionManager, verbose=False):

        def updateSessionItem(session_item:SessionItem):
            if not session_item.anilist_id:
                foundAnime = self.search(session_item.title)
                if foundAnime:
                    session_item.anilist_id = foundAnime.anilist_id
                    session_item.episodesInTotal = foundAnime.episodesInTotal
                    return

            episodesInTotal = self.getTotalEpisodesCount(title=session_item.title, id=session_item.anilist_id)

            session_item.episodesInTotal = episodesInTotal or session_item.episodesInTotal

        pbar = None
        if verbose:
            pbar = ProgressBar(total=len(session.session_items), postfix='Sincronizando com Anilist', leave=False)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(updateSessionItem, session_item) for session_item in session.session_items]
            for _ in as_completed(futures):
                if pbar:
                    pbar.update(1)

        if pbar:
            pbar.close()

    def get_watching(self) -> List[SessionItem]:
        variables = {
            'userName': self.username
        }
        query = '''
        query ($userName: String) {
          Page(page: 1, perPage: 20) {
            mediaList(userName: $userName, status_in: [CURRENT, REPEATING], type: ANIME) {
              progress
              media {
                id
                nextAiringEpisode {
                    episode
                }
                title {
                  romaji
                }
                episodes
                duration
              }
            }
          }
        }
        '''
        result = self._request(query, variables)
        result = result['data']['Page']['mediaList']

        watch_list: List[SessionItem] = []


        for item in result:
            media = item['media']
            watch_list.append(
                SessionItem(
                    Anime(media['title']['romaji'], media['title']['romaji']),
                    media['episodes'],
                    media['nextAiringEpisode']['episode'] if media['nextAiringEpisode'] else media['episodes'],
                    item['progress'],
                    '',
                    anilist_id=media['id'],
                    duration=media['duration']*60
                )
            )

        return watch_list

    def set_watching(self, session_list:List[SessionItem]):
        query = '''
            mutation ($mediaId: Int, $progress: Int, $status: MediaListStatus) {
              SaveMediaListEntry (mediaId: $mediaId, progress: $progress, status: $status) {
                  progress
                  status
              }
            }
        '''

        try:
            with progress(total=len(session_list), postfix='Sincronizando', leave=False) as pbar:
                for session_item in session_list:
                    id = session_item.anilist_id

                    try:
                        if not id:
                            id = self.search(session_item.title).anilist_id
                    except AnimeNotFound:
                        if not self.silent:
                            error(f"Não foi possível sincronizar '{session_item.title}'", clearline=True)
                        continue

                    variables = {
                        'mediaId': id,
                        'progress': session_item.lastEpisode,
                        'status': 'COMPLETED' if session_item.status == 'complete' else 'CURRENT'
                    }

                    self._request_mutate(query, variables)
                    pbar.update(1)
        except KeyboardInterrupt:
            pass

    def merge_session(self, session:SessionManager, preferRemote=False):
        watch_list = self.get_watching()

        intersecting_items:List[SessionItem] = []
        new_items:List[SessionItem] = []

        for watch_item in watch_list:
            if session.has_anime(watch_item.anime):
                intersecting_items.append(watch_item)
            else:
                new_items.append(watch_item)

        if preferRemote:
            for watch_item in intersecting_items:
                session.update(watch_item.anime, watch_item.lastEpisode, watch_item.watchTime, watch_item.duration)

        session.add_session_items(new_items)

    def _request(self, query, variables):
        if not self.username:
            raise MissingUsername("Missing anilist username")
        res = requests.post(
            'https://graphql.anilist.co',
            json = {
                'query': query,
                'variables': variables
            }
        )
        return res.json()

    def _request_mutate(self, query, variables):
        if not self.token:
            raise MissingToken("Missing anilist token")
        res = requests.post(
            'https://graphql.anilist.co',
            headers={
                'Authorization': 'Bearer '+self.token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json = {
                'query': query,
                'variables': variables
            }
        )
        return res.json()

    def login(self):

        webbrowser.open(f'https://anilist.co/api/v2/oauth/authorize?client_id={self._client_id}&response_type=token')

        from http.server import HTTPServer, SimpleHTTPRequestHandler

        hostName = "localhost"
        serverPort = 8000

        def set_token(token):
            self.token = token

        class MyServer(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
                    self.wfile.write(bytes("""
                       <html><head><title></title></head>
                         <script defer>
                            const token = window.location.hash.split('&')[0].replace('#','')
                           window.location.href = "/public/oauth.html?"+token
                         </script>
                       </html>""", "utf-8"))
                elif 'oauth' in self.path:
                    token = self.path.split('?')[1].split('=')[1]
                    set_token(token)
                    
                    SimpleHTTPRequestHandler.do_GET(self) 
                    raise KeyboardInterrupt()

        webServer = HTTPServer((hostName, serverPort), MyServer)

        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

        webServer.server_close()


