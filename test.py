from manager import Manager

manager = Manager()


url = manager.search('boku no hero')[0].scrapers
print(url)

# print(goyabu.episodes(url)[0].availableLanguages())



