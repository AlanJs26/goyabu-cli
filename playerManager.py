from os import path,system
from time import sleep
from typing import List, Tuple, TypedDict
from scraper import Episode
from dropdown import isWindows

class PlayerManagerResults(TypedDict):
    lastEpisode:int
    watchTime:int

class PlayerManager():
    def __init__(self, title:str, scraperName:str, episodes:List[Episode], root='', playlistPos=0):
        self.scraperName = scraperName
        self.playlistPos = playlistPos
        self.root = root
        self.title = title
        self.episodes = episodes

    def isMpvAvailable(self) -> bool:
        return True

    def playWithMPV(self, path:str) -> PlayerManagerResults:
        from python_mpv_jsonipc import MPV

        if isWindows:
            mpv = MPV()
        else:
            mpv = MPV(ipc_socket="/tmp/mpv-socket")

        mpvEpIndex = 1 # Current anime playing 

        # Update mpvEpIndex with the current episode every time a new episodes begin
        @mpv.property_observer('media-title')
        def media_title_ob(name, value):
            if not name or not value or 'Ep ' not in value: return
            global mpvEpIndex
            mpvEpIndex = int(value.split('-')[0].replace('Ep ', ''))


        # -----
        mpv.playlist_pos = 0
        mpv.play(path)
        mpv.command('keypress', 'space')
        sleep(2)
        mpv.command('playlist-play-index', self.playlistPos)
        mpv.command('keypress', 'space')

        while mpv.wait_for_property('playlist-play-index') != 'none':
            pass

        return {"lastEpisode": mpvEpIndex, "watchTime": int(mpv.playback_time)}

    def play(self, path:str, player_path:str) -> PlayerManagerResults:
        system(f'{player_path} "{path}"')

        return {"lastEpisode": 1, "watchTime": 0}

    def generatePlaylistFile(self) -> str:
        fileText = '#EXTM3U\n\n' 
        resolutionRanking = ['ultra-hd', 'full-hd', 'hd', 'sd']

        for index,episode in enumerate(self.episodes):
            fileText+=f'#EXTINF:-1,Ep {index+1} - {episode.title.replace("#", "")}\n'
            sorted_links = sorted(episode.getLinksBySource(self.scraperName), key=lambda x:resolutionRanking.index(x.quality))
            for link in sorted_links:
                fileText+=f'{link.url}\n'

        file_path = path.join(self.root, self.title+".m3u")

        with open(file_path, 'w') as file:
            file.writelines(fileText)


        return file_path
