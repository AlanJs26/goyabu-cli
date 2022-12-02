from manager import Manager
from dropdown import interactiveTable
from sessionManager import SessionManager

sessionmanager = SessionManager()

# print(sessionmanager.session_items)
session_item = sessionmanager.select()
if isinstance(session_item,str):
    print(session_item)
else:
    print(session_item.title)

# manager = Manager()
#
# animes = manager.search('boku no hero')
#
# anime_names = [['',anime.title] for anime in animes]
#
# results = interactiveTable(
#     anime_names,
#     ['','Animes'],
#     'll',
#     maxListSize=7,
#     highlightRange=(0,1),
#     width=20,
#     flexColumn=1
# )
#
# if results['selectedPos'] is None:
#     print(results)
#     exit()
#
# anime = animes[results['selectedPos']]
# print(anime.scrapers)
#
# episodes = anime.retrieveEpisodes()
# episodes_names = [[episode.id, episode.title] for episode in episodes]
#
# results = interactiveTable(
#     episodes_names,
#     ['Id','Episodios'],
#     'll',
#     maxListSize=7,
#     highlightRange=(0,1),
#     width=20,
#     flexColumn=1
# )
#
# if results['selectedPos'] is None or results['selectedItem'] is None:
#     print(results)
#     exit()
#
# # print([item.url for item in episodes[results['selectedPos']].sources[0][1]])
# for link in episodes[results['selectedPos']].getLinks(anime.source):
#     print(link)
#
# sessionmanager.add([anime])
#
# sessionmanager.update(anime, int(results['selectedItem'][0]), 300)
#
# sessionmanager.dump()


# print(goyabu.episodes(url)[0].availableLanguages())



