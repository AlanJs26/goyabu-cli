from  http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List
from urllib.parse import parse_qs
import socket
from animeScrapper import animeInfo

rawtext = ''
PORT = 8000

def getLocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    return ip

localIp = getLocalIP()

def generatePlaylist(animelist:List[str]):
    fileText = '#EXTM3U\n\n'
    for anime in animelist:
        epNum = animeInfo('episodesNum', query=anime, engines=['goyabu'])

        for ep in range(1, list(epNum.values())[0]+1):
            fileText+=f'#EXTINF:-1,Ep {ep} - {anime.replace(",", "")}\n'
            fileText+=f'http://{localIp}:8000/?q={anime.replace(",", "ççç")}&e={ep-1}\n\n'
    return fileText

class Server(BaseHTTPRequestHandler):

    def do_GET(self):
        global rawtext

        print(self.path)
        

        if(self.path == '/'):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = rawtext

            # Writing the HTML contents with UTF-8
            self.wfile.write(bytes(html, "utf8"))

            return
       
        if '?q=' in self.path or '&q=' in self.path:
            parameters = parse_qs(self.path[2:])
            q = parameters['q'][0].replace('ççç', ',')
            e = 1
            engine = 'goyabu'

            if 'e' in parameters:
                e = parameters['e'][0]

            if 'engine' in parameters:
                engine = parameters['engine'][0]

            episodes = animeInfo('episodes', query=q, range=[e], engines=[engine])
            links = list(episodes[engine].values())

            #  self.send_response(200)
            #  self.send_header("Content-type", "text/html")
            #  self.end_headers()
            #  self.wfile.write(bytes('Alan', "utf8"))
            self.send_response(302)
            self.send_header("Location", links[0])
            self.end_headers()

        return

def serveRawText(text:str):
    global rawtext
    rawtext = text

    http_handler = Server

    my_server = HTTPServer(("", PORT), http_handler)
    print(f"serving playlist at: {localIp}:{PORT}")

    # Star the server
    try:
        my_server.serve_forever()
    except KeyboardInterrupt:
        exit()

if __name__ == "__main__":
    import sys
    arg = sys.argv[-1]

    with open(arg) as text:
        serveRawText(text.read())

    #  serveRawText(generatePlaylist(['yuukaku']))

