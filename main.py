from scraperManager import ScraperManager
from sessionManager import SessionManager
from playerManager import PlayerManager
from dropdown import interactiveTable, HighlightedTable
from typing import Dict
import termtables as tt


def mainTUI(default_anime_name:str, default_player:str, default_range:Dict[str,int], default_root:str, always_yes:bool):
    manager = ScraperManager()
    sessionmanager = SessionManager(scrapers=manager.scrapers, root=default_root)

    session_item = default_anime_name or sessionmanager.select()

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
        raise Exception(f'Cannot find any episode for {anime.title}')

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
            episodes = [episodes[i] for i in results['items']]

        for episode in episodes:
            episode.retrieveLinks(anime.source)
    else:
        episodes = episodes[slice(default_range['start'], default_range['end'])]


    player = PlayerManager(anime.title, anime.source, episodes)

    playlist_file = player.generatePlaylistFile()

    print(f'Abrindo "{playlist_file}"...')

    if player.isMpvAvailable() and default_player == 'mpv':
        results = player.playWithMPV(playlist_file)
    else:
        results = player.play(playlist_file, default_player)


    sessionmanager.add([anime])

    sessionmanager.update(anime, results['lastEpisode'], results['watchTime'])

    sessionmanager.dump()





