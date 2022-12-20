from .scraperManager import ScraperManager
from .sessionManager import SessionManager
from .playerManager import PlayerManager
from .dropdown import interactiveTable
from .translation import t, error
import termtables as tt
from typing import Dict, Union, List
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def mainTUI(default_anime_name:str, default_player:str, episodes_range:Dict[str,Union[None,int]], default_root:str, always_yes:bool, default_scraper:List[str]):
    manager = ScraperManager()
    sessionmanager = SessionManager(scrapers=manager.scrapers, root=default_root)

    session_item = sessionmanager.select(query=default_anime_name, maxListSize=10)

    if isinstance(session_item,str):
        animes = manager.search(session_item, default_scraper)

        if not animes:
            error(t("Nenhum anime encontrado com o nome '{}'", session_item))
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

            if results['selectedItem'] is None:
                raise Exception(t('Não foi possível selecionar uma fonte'))

            anime.source = results['selectedItem'][1]
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


        if results['text'] not in ['', 'S', 's']:
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

            if results['items'] is None:
                print(t("É possível selecionar os episódios usando 'c' ou a barra de espaço"))
                exit()

        if results['items']:
            episodes_range['start'] = min(results['items'].keys())
            episodes_range['end'] = max(results['items'].keys())

            episodes = [episodes[i] for i in results['items']]
    elif is_range_valid(episodes_range):
        episodes = episodes[slice(episodes_range['start'], episodes_range['end'])]


    with tqdm(total=len(episodes), postfix=t("Links carregados"), ascii=True, leave=False, bar_format='|{bar}| {n_fmt}/{total_fmt}{postfix}') as pbar:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(episode.retrieveLinks,anime.source) for episode in episodes]
            for _ in as_completed(futures):
                pbar.update(1)

    for episode in episodes:
        if not episode.getLinksBySource(anime.source):
            error(t('Não foi encontrado nenhum link válido para o episódio {}', episode.index+1))


    player = PlayerManager(anime.title, anime.source, episodes, root=default_root)

    playlist_file = player.generatePlaylistFile()

    if not playlist_file:
        error(t('Não foi possível gerar o arquivo m3u'))
        exit()

    print(t('Abrindo "{}"...', playlist_file))

    if player.isMpvAvailable() and default_player == 'mpv':
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
        results = player.play(playlist_file, default_player)


    sessionmanager.add([anime])

    sessionmanager.update(anime, results['lastEpisode'], results['watchTime'], results['duration'])

    print(t('Atualizando o histórico...'))
    sessionmanager.dump(verbose=True, number_to_update=10)





