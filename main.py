from scraperManager import ScraperManager
from sessionManager import SessionManager
from playerManager import PlayerManager
from dropdown import interactiveTable
from typing import Dict
import termtables as tt


def mainTUI(default_anime_name:str, default_player:str, episodes_range:Dict[str,int], default_root:str, always_yes:bool):
    manager = ScraperManager()
    sessionmanager = SessionManager(scrapers=manager.scrapers, root=default_root)

    session_item = sessionmanager.select(query=default_anime_name)

    if isinstance(session_item,str):
        animes = manager.search(session_item)

        if not animes:
            print(f"Nenhum anime encontrado com o nome '{session_item}'")
            exit()

        anime_names = [['',anime.title, ','.join(anime.pageUrl.keys())] for anime in animes]

        if not always_yes:
            results = interactiveTable(
                anime_names,
                ['','Animes', 'Fonte'],
                'llc',
                maxListSize=7,
                highlightRange=(2,2),
                width=20,
                flexColumn=1
            )

            if results['selectedPos'] is None:
                print(results)
                exit()

            anime = animes[results['selectedPos']]
        else:
            anime = animes[0]
    else:
        anime = session_item.anime


    tt.print(
        [[anime.title]],
        header=["Anime Selecionado"],
        style=tt.styles.rounded,
        alignment="c",
    )

    if len(anime.availableScrapers) > 1:
        if not always_yes:
            results = interactiveTable(
                [['',scraperName] for scraperName in anime.availableScrapers],
                ['','Escolha uma fonte'],
                'll',
                behaviour='single',
                maxListSize=10,
                highlightRange=(0,1),
                width=20,
                flexColumn=1
            )

            if results['selectedItem'] is None:
                raise Exception('Cannot select scraper')

            anime.source = results['selectedItem'][1]
        else:
            anime.source = anime.availableScrapers[0]


    episodes = anime.retrieveEpisodes()
    episodes_names = [['', episode.title] for episode in episodes]

    if not episodes:
        print(f"Não foi possível acessar os episódios de '{anime.title}' usando '{anime.source}'")
        exit()

    if not always_yes:
        results = interactiveTable(
            episodes_names,
            ['','Episodios'],
            'll',
            behaviour='multiSelectWithText',
            maxListSize=13,
            highlightRange=(1,1),
            width=20,
            flexColumn=1,
            hintText='deseja assistir todos os episódios? [S/n]: '
        )


        if results['text'] not in ['', 'S', 's']:
            results = interactiveTable(
                episodes_names,
                ['','Episodios'],
                'll',
                behaviour='multiSelect',
                maxListSize=13,
                highlightRange=(1,1),
                width=20,
                flexColumn=1
            )

            if results['items'] is None:
                print("É possível selecionar os episódios usando 'c' ou a barra de espaço")
                exit()

        if results['items']:
            episodes_range['start'] = min(results['items'].keys())
            episodes_range['end'] = max(results['items'].keys())

            episodes = [episodes[i] for i in results['items']]
    elif episodes_range['end'] - episodes_range['start'] != 0:
        episodes = episodes[slice(episodes_range['start'], episodes_range['end'])]

    for episode in episodes:
        episode.retrieveLinks(anime.source)

    session_anime = sessionmanager.find(anime)

    player = PlayerManager(anime.title, anime.source, episodes)

    playlist_file = player.generatePlaylistFile()

    print(f'Abrindo "{playlist_file}"...')

    if player.isMpvAvailable() and default_player == 'mpv':
        if session_anime:
            last_watch_pos = session_anime.lastEpisode
            seek_time = session_anime.watchTime
        else:
            last_watch_pos = 0
            seek_time = 0

        ep_ids = [ep.index for ep in episodes]
        start_pos = 0
        if last_watch_pos-1 in ep_ids:
            start_pos = ep_ids.index(last_watch_pos-1)

        results = player.playWithMPV(playlist_file, seek_time=seek_time, playlistPos=start_pos)
    else:
        results = player.play(playlist_file, default_player)


    sessionmanager.add([anime])

    sessionmanager.update(anime, results['lastEpisode'], results['watchTime'])

    # sessionmanager.dump()





