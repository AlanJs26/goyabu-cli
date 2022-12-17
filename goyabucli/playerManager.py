from os import path,system,makedirs
from time import sleep
from typing import List, TypedDict
from goyabucli.scraper import Episode
from goyabucli.dropdown import isWindows

class PlayerManagerResults(TypedDict):
    lastEpisode:int
    watchTime:int
    duration:int

class PlayerManager():
    def __init__(self, title:str, scraperName:str, episodes:List[Episode], root='', playlistPos=0):
        self.scraperName = scraperName
        self.playlistPos = playlistPos
        self.root = root
        self.title = title
        self.episodes = episodes

        self.playlist_folder = path.join(root,'playlists/')

        if not path.isdir(self.playlist_folder):
            makedirs(self.playlist_folder, exist_ok=True)


    def isMpvAvailable(self) -> bool:
        return True

    def playWithMPV(self, path:str, seek_time=0, playlistPos=0) -> PlayerManagerResults:
        from python_mpv_jsonipc import MPV

        if isWindows:
            mpv = MPV()
        else:
            mpv = MPV(ipc_socket="/tmp/mpv-socket")

        mpvEpIndex = 1 # Current anime playing 

        # -----
        mpv.playlist_pos = 0
        mpv.play(path)

        mpv.pause = True
        
        timeout = 0
        while (not mpv.media_title or not mpv.seekable) and timeout < 100:
            sleep(0.2)
            timeout += 1

        if playlistPos:
            mpv.command('playlist-play-index', playlistPos)

            timeout = 0
            while (not mpv.media_title or not mpv.seekable or mpv.playlist_playing_pos != playlistPos) and timeout < 100 :
                sleep(0.2)
                timeout += 1

            mpv.time_pos = seek_time

        mpv.pause = False
        duration = mpv.duration

        working=False

        try:
            while mpv.media_title:
                sleep(1)
                seek_time = mpv.playback_time

                if not mpv.media_title or 'Ep ' not in mpv.media_title:
                    continue
                mpvEpIndex = int(mpv.media_title.split('-')[0].replace('Ep ', ''))
                duration = mpv.duration
                working=True
        except:
            pass

        if not working:
            print('\nparece que o link deste anime não está funcionando :(\nTente um anime diferente.')

        try:
            mpv.command('quit')
        except:
            print('Saindo do MPV...')

        return {"lastEpisode": mpvEpIndex, "watchTime": int(seek_time or 0), "duration": int(duration or 0)}

    def play(self, path:str, player_path:str) -> PlayerManagerResults:
        system(f'{player_path} "{path}"')

        return {"lastEpisode": 1, "watchTime": 0, "duration": 0}

    def generatePlaylistFile(self) -> str:
        fileText = '#EXTM3U\n\n' 
        resolutionRanking = ['ultra-hd', 'full-hd', 'hd', 'sd']

        for episode in self.episodes:
            fileText+=f'#EXTINF:-1,Ep {episode.id} - {episode.title.replace("#", "")}\n'
            sorted_links = sorted(episode.getLinksBySource(self.scraperName), key=lambda x:resolutionRanking.index(x.quality))

            fileText+=f'{sorted_links[0].url}\n'
            # for link in sorted_links:
            #     fileText+=f'{link.url}\n'

        file_path = path.join(self.playlist_folder, self.title+".m3u")

        with open(file_path, 'w') as file:
            file.writelines(fileText)


        return file_path
