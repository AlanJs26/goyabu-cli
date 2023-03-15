from os import path,system,makedirs
from time import sleep
from typing import List, TypedDict, Optional
from .scraper import Episode
from .dropdown import isWindows
from .utils import headers

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
        self.headers_per_ep = []

        self.playlist_folder = path.join(root,'playlists/')

        if not path.isdir(self.playlist_folder):
            makedirs(self.playlist_folder, exist_ok=True)


    def isMpvAvailable(self) -> bool:
        from shutil import which

        return which('mpv') is not None

    def playWithMPV(self, path:str, seek_time=0, playlistPos=None) -> PlayerManagerResults:
        from python_mpv_jsonipc import MPV
        print('starting MPV')

        if isWindows:
            mpv = MPV(user_agent=headers['User-Agent'])
        else:
            mpv = MPV(ipc_socket="/tmp/mpv-socket", user_agent=headers['User-Agent'])

        mpvEpIndex = 1 # Current anime playing 

        # -----
        mpv.playlist_pos = 0
        header_fields = self.headers_per_ep[0]
        mpv.command('set_property', 'options/http-header-fields', header_fields)
        mpv.play(path)

        mpv.pause = True

        print('waiting MPV...')
        
        timeout = 0
        while (not mpv.media_title or not mpv.seekable) and timeout < 100:
            sleep(0.2)
            timeout += 1

        if playlistPos is not None:
            print('waiting media...')
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
            print(f'playing {mpv.media_title}')
            while mpv.media_title:
                sleep(1)
                seek_time = mpv.playback_time

                if not mpv.media_title or 'Ep ' not in mpv.media_title:
                    continue

                mpvEpIndex = int(mpv.media_title.split('-')[0].replace('Ep ', ''))
                playlistPos = mpv.playlist_playing_pos
                if isinstance(playlistPos, int):
                    header_fields = self.headers_per_ep[playlistPos]
                    mpv.command('set_property', 'options/http-header-fields', header_fields)
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

    def generatePlaylistFile(self, playlist_basename:Optional[str]=None) -> str:
        fileText = '' 
        resolutionRanking = ['ultra-hd', 'full-hd', 'hd', 'sd']

        for episode in self.episodes:
            if not episode.getLinksBySource(self.scraperName):
                continue
            fileText+=f'#EXTINF:-1,Ep {episode.id} - {episode.title.replace("#", "")}\n'
            
            sorted_links = sorted(episode.getLinksBySource(self.scraperName), key=lambda x:resolutionRanking.index(x.quality))

            fileText+=f'{sorted_links[0].url}\n'
            self.headers_per_ep.append(
                ','.join(f'{k}: {v}' for k,v in sorted_links[0].headers.items() if k != 'User-Agent')
            )
            # for link in sorted_links:
            #     fileText+=f'{link.url}\n'

        if not fileText:
            return ''

        if not playlist_basename:
            playlist_basename = self.title

        file_path = path.join(self.playlist_folder, playlist_basename+".m3u")

        with open(file_path, 'w') as file:
            file.writelines(f'#EXTM3U\n\n{fileText}')


        return file_path
