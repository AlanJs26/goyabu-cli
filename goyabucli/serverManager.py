from  http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote
from typing import List
import socket

from goyabucli.sessionManager import SessionItem
from goyabucli.translation import error
from goyabucli.utils import headers


class ServerManager():

    def __init__(self, sessionItems:List[SessionItem], port=8080):
        self.sessionItems = sessionItems
        self.port = port
        self.ip = self.getIP()
        self.playlistText = self.generatePlaylistFile()

    def getIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        return ip

    def generatePlaylistFile(self):
        fileText = '#EXTM3U\n\n'
        for sessionItem in self.sessionItems:

            for episode in sessionItem.anime.retrieveEpisodes(supress=True):
                fileText+=f'#EXTINF:-1,Ep {episode.id} - {sessionItem.title}\n'
                fileText+=f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n'

                fileText+=f'http://{self.ip}:{self.port}/?q={quote(sessionItem.id)}&e={episode.index}\n\n'
        return fileText
    
    def serve(self):
        server = HTTPServer(("",self.port), self._get_handler(self.playlistText, self.sessionItems))
        print(f"serving playlist at: {self.ip}:{self.port}")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return self.sessionItems

    def _get_handler(self, playlistText:str, sessionItems:List[SessionItem]):
        class _server(BaseHTTPRequestHandler):
            def do_GET(self):
                if(self.path == '/'):
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()

                    # Writing the HTML contents with UTF-8
                    self.wfile.write(bytes(playlistText, "utf8"))
               
                elif '?q=' in self.path or '&q=' in self.path:
                    try:
                        parameters = parse_qs(self.path[2:])
                        q = parameters['q'][0]
                        e = int(parameters['e'][0])

                        foundItem = next(item for item in sessionItems if quote(item.id) == quote(q))

                        if len(foundItem.anime.episodes):
                            episodes = list(foundItem.anime.episodes.values())
                        else:
                            episodes = foundItem.anime.retrieveEpisodes()

                        episodes[e].retrieveLinks(foundItem.anime.source)

                        links = episodes[e].getLinksBySource(foundItem.anime.source)
                        
                        foundItem.lastEpisode = e+1

                        location = links[0].url
                        self.send_response(302)
                        self.send_header("Location", location)
                        self.end_headers()
                    except Exception as e:
                        error(str(e))
                        self.send_response(404)
        return _server


    
