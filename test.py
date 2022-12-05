from scraperManager import ScraperManager
from sessionManager import SessionManager
from playerManager import PlayerManager
from dropdown import interactiveTable, HighlightedTable
import termtables as tt

manager = ScraperManager()
sessionmanager = SessionManager(scrapers=manager.scrapers)

session_item = sessionmanager.select()

if isinstance(session_item,str):
    animes = manager.search('boku no hero')

    anime_names = [['',anime.title] for anime in animes]

    results = interactiveTable(
        anime_names,
        ['','Animes'],
        'll',
        maxListSize=7,
        highlightRange=(0,1),
        width=20,
        flexColumn=1
    )

    if results['selectedPos'] is None:
        print(results)
        exit()

    anime = animes[results['selectedPos']]
else:
    anime = session_item.anime


tt.print(
    [[anime.title]],
    header=["Anime Selecionado"],
    style=tt.styles.rounded,
    alignment="c",
)

if len(anime.availableScrapers) > 1:
    results = interactiveTable(
        [[scraperName] for scraperName in anime.availableScrapers],
        ['Escolha uma fonte'],
        'll',
        behaviour='single',
        maxListSize=10,
        highlightRange=(0,1),
        width=20,
        flexColumn=1
    )

    if results['selectedItem'] is None:
        raise Exception('Cannot select scraper')

    anime.source = results['selectedItem'][0]


episodes = anime.retrieveEpisodes()
episodes_names = [['', episode.title] for episode in episodes]

if not episodes:
    raise Exception(f'Cannot find any episode for {anime.title}')

table = HighlightedTable(
    episodes_names,
    ['', "Episódios"],
    [],
    'cl',
    highlightRange=(1,1),
    maxListSize=13,
)
table.update()
table.cursorToEnd(0)

choice = str(input("deseja assistir todos os episódios? [S/n]: "))

if choice not in ['', 'S', 's']:
    table.cursorToBeginning(1)
    table.clear()

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
        print("You can items with 'c' or 'spacebar'")
        exit()

    episodes = [episodes[i] for i in results['items']]

for episode in episodes:
    episode.retrieveLinks(anime.source)

player = PlayerManager(anime.title, anime.source, episodes)

playlist_file = player.generatePlaylistFile()

print(f'Abrindo "{playlist_file}"...')

if player.isMpvAvailable():
    results = player.playWithMPV(playlist_file)
else:
    results = player.play(playlist_file, 'mpv')


sessionmanager.add([anime])

sessionmanager.update(anime, results['lastEpisode'], results['watchTime'])

sessionmanager.dump()





