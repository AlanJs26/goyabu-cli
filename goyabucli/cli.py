from goyabucli.anilistManager import AnilistManager
from .scraperManager import ScraperManager
from .anilistManager import AnilistManager, MissingToken
from .sessionManager import SessionManager, SessionItem
from .playerManager import PlayerManager
from .dropdown import Highlight, interactiveTable
from .translation import t, error, warning
from .progress import progress
import termtables as tt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Union, List
from dataclasses import asdict,dataclass
from sys import stdout
from os import path
import json

@dataclass
class Config:
    anilist_username:str
    token:str
    config_dir:str
    player:str
    silent:bool

def mainTUI(anilistManager:AnilistManager, default_anime_name:str, episodes_range:Dict[str,Union[None,int]], always_yes:bool, default_scraper:List[str], config=Config('','','','', False)):
    manager = ScraperManager()
    sessionmanager = SessionManager(scrapers=manager.scrapers, root=config.config_dir)

    selected_item = sessionmanager.select(query=default_anime_name, maxListSize=10)

    if isinstance(selected_item,str) or (isinstance(selected_item,SessionItem) and not selected_item.lastSource):
        anime_title = selected_item if isinstance(selected_item,str) else selected_item.title 
        animes = manager.search(anime_title, default_scraper)

        if not animes:
            error(t("Nenhum anime encontrado com o nome '{}'", anime_title))
            exit()

        anime_names = [['',anime.title, ','.join(anime.pageUrl.keys())] for anime in animes]

        if not always_yes:
            results = interactiveTable(
                anime_names,
                ['',t('Animes'), t('Fonte')],
                'llc',
                maxListSize=7,
                highlightRange=(2,2),
                width=20,
                flexColumn=1
            )

            if results.selectedPos is None:
                print(results)
                exit()

            anime = animes[results.selectedPos]
        else:
            anime = animes[0]
    else:
        anime = selected_item.anime


    tt.print(
        [[anime.title]],
        header=[t("Anime Selecionado")],
        style=tt.styles.rounded,
        alignment="c",
    )

    def is_range_valid(episodes_range:Dict[str,Union[None,int]]):
        return (
            episodes_range['start'] is None or
            episodes_range['end'] is None or
            (episodes_range['end'] != episodes_range['start'])
        )


    session_anime = sessionmanager.find(anime)

    if session_anime and not is_range_valid(episodes_range):
        episodes_range['start'] = session_anime.lastEpisode-1
        episodes_range['end'] = None

    if len(anime.availableScrapers) > 1:
        if not always_yes:
            results = interactiveTable(
                items=[['',scraperName] for scraperName in anime.availableScrapers],
                header=['',t('Escolha uma fonte')],
                alignment='ll',
                behaviour='single',
                maxListSize=10,
                highlightRange=(0,1),
                width=20,
                flexColumn=1
            )

            if results.selectedItem is None:
                raise Exception(t('Não foi possível selecionar uma fonte'))

            anime.source = results.selectedItem[1]
        else:
            anime.source = anime.availableScrapers[0]


    episodes = anime.retrieveEpisodes()
    episodes_names = [['', episode.title] for episode in episodes]

    if not episodes:
        error(t("Não foi possível acessar os episódios de '{}' usando '{}'", anime.title, anime.source))
        exit()

    if (not always_yes and not is_range_valid(episodes_range)) or not is_range_valid(episodes_range):
        results = interactiveTable(
            items=episodes_names,
            header=['',t('Episodios')],
            alignment='ll',
            behaviour='multiSelectWithText',
            maxListSize=13,
            highlightRange=(1,1),
            width=20,
            flexColumn=1,
            hintText=t('deseja assistir todos os episódios? [S/n]: ')
        )


        if results.text not in ['', 'S', 's']:
            results = interactiveTable(
                items=episodes_names,
                header=['',t('Episodios')],
                alignment='ll',
                behaviour='multiSelect',
                maxListSize=13,
                highlightRange=(1,1),
                width=20,
                flexColumn=1
            )

            if results.items is None:
                print(t("É possível selecionar os episódios usando 'c' ou a barra de espaço"))
                exit()

        if results.items:
            episodes_range['start'] = min(results.items.keys())
            episodes_range['end'] = max(results.items.keys())

            episodes = [episodes[i] for i in results.items]
    elif is_range_valid(episodes_range):
        episodes = episodes[slice(episodes_range['start'], episodes_range['end'])]


    with progress(total=len(episodes), postfix=t("Links carregados"), leave=False) as pbar:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(episode.retrieveLinks,anime.source) for episode in episodes]
            for _ in as_completed(futures):
                pbar.update(1)

    for episode in episodes:
        if not episode.getLinksBySource(anime.source):
            error(t('Não foi encontrado nenhum link válido para o episódio {}', episode.index+1))


    player = PlayerManager(anime.title, anime.source, episodes, root=config.config_dir)

    playlist_file = player.generatePlaylistFile()

    if not playlist_file:
        error(t('Não foi possível gerar o arquivo m3u'))
        exit()

    print(t('Abrindo "{}"...', playlist_file))

    if player.isMpvAvailable() and config.player == 'mpv':
        start_pos = 0
        last_watch_pos = 0
        seek_time = 0

        # restore previous session
        ep_ids = [ep.index for ep in episodes]
        if session_anime and session_anime.lastEpisode-1 in ep_ids:
            last_watch_pos = session_anime.lastEpisode
            seek_time = session_anime.watchTime
            start_pos = ep_ids.index(last_watch_pos-1)

            # jump to next episode if user stopped at the end of the episode of the previous session
            time_until_ep_ends = session_anime.duration-seek_time
            if time_until_ep_ends > 0 and time_until_ep_ends < 90:
                start_pos += 1
                seek_time = 0


        results = player.playWithMPV(playlist_file, seek_time=seek_time, playlistPos=start_pos)
    else:
        results = player.play(playlist_file, config.player)


    sessionmanager.add([anime])

    sessionmanager.update(anime, results['lastEpisode'], results['watchTime'], results['duration'])

    try:
        anilistManager.merge_session(sessionmanager)
    except MissingToken:
        if not config.silent:
            warning("wasn't possible sync with anilist. Missing authentification token")
            warning("to get rid of this message, mark the option 'silent' to True in the config")
            warning("    eg: anime --config")

    print(t('Atualizando o histórico...'))
    anilistManager.update_session(sessionmanager, True)
    sessionmanager.dump(verbose=True, number_to_update=10)

    anime_session_item = sessionmanager.find(anime)

    if anime_session_item:
        anilistManager.set_watching([anime_session_item])



def configTUI(config: Config, anilistManager:AnilistManager):
    print("Use 'q' para sair\n")
    
    while True:
        config_dict = {
            'Anilist Status': ('Ready' if config.token else 'Missing Token (press Enter to login)'),
            'Anilist username': config.anilist_username,
            'Config directory': config.config_dir,
            'Player': config.player,
            'Silent': config.silent,
        }
        rows = [ [key, value] for key,value in  config_dict.items() ]

        results = interactiveTable(
            rows,
            ['Field', 'Value'],
            "cc",
            highlightRange=(0,2),
            staticHighlights=[Highlight(0, 'green' if config.token else 'fail')],
            flexColumn=2
        )

        if not results.selectedItem:
            break

        def change_field(field):
            try:
                new_value = str(input(f"Novo valor para '{field}': "))
                stdout.write('\033[A\r\033[K')
            
                setattr(config, field, new_value)
            except KeyboardInterrupt:
                pass

        if results.selectedItem[0] == 'Anilist Status':
            anilistManager.login()
            config.token = anilistManager.token
        elif results.selectedItem[0] == 'Anilist username':
            change_field('anilist_username')
        elif results.selectedItem[0] == 'Config directory':
            change_field('config_dir')
        elif results.selectedItem[0] == 'Player':
            change_field('player')
        elif results.selectedItem[0] == 'Silent':

            selected = interactiveTable(
                [
                    ['','True'],
                    ['','False'],
                ],
                ['','Silent'],
                "cl",
                highlightRange=(0,1),
                staticHighlights=[
                    Highlight(0, 'green'),
                    Highlight(1, 'fail'),
                ],
            )
            if not selected.selectedItem:
                break

            if selected.selectedItem[1] == 'True':
                config.silent = True
            else:
                config.silent = False


        with open(path.join(config.config_dir, 'config.json'), 'w') as file:
            json.dump(asdict(config), file, indent=2)






