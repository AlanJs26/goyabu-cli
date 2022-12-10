from functools import wraps
from multiprocessing import Process
from os import get_terminal_size

from anilist import Client

#  def parametrized(dec):
    #  def layer(*args, **kwargs):
        #  def repl(f):
            #  return dec(f, *args, **kwargs)
        #  return repl
    #  return layer

#  @parametrized
#  def infoDecorator(f, outputs):
    #  def aux(*xs, **kws):
        #  difference = list(set(xs).difference(outputs))
        #  if len(difference) > 1:
            #  raise SystemExit(f"'{' and '.join(difference)}' are not valid outputs")
        #  elif len(difference):
            #  raise SystemExit(f"'{difference[0]}' is not a valid output")

        #  result = f(*xs, **kws)

        #  return result if len(result)>1 else list(result.items())[0][1]
    #  return aux

anilistClient = Client()
search_buffer = {}

def getTotalEpisodesCount(title:str):
    try:
        result = anilistClient.search_anime(title,1)

        if not result:
            return 0
        
        searchResult = result[0]
        foundAnime = anilistClient.get_anime(searchResult.id)

        return foundAnime.episodes
    except:
        return 0

def animeTitle2Id(title:str):
    return title
    # try:
    #     result = anilistClient.search_anime(title,1)
    #
    #     if not result:
    #         return 0
    #     
    #     searchResult = result[0]
    #     foundAnime = anilistClient.get_anime(searchResult.id)
    #
    #     return foundAnime.title.romaji
    # except:
    #     return title

def nameTrunc(text, length):
    columns = get_terminal_size().columns
    if columns < length:
        nameSlice = slice(None, len(text)-(length-columns))
        return text[nameSlice]+'...'
    return text

def infoDecorator(outputs):
    def real_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            possibleOutputs = [*outputs, 'capabilities']

            difference = list(set(args).difference(possibleOutputs))
            if len(difference) > 1:
                raise SystemExit(f"'{' and '.join(difference)}' are not valid outputs")
            elif len(difference):
                raise SystemExit(f"'{difference[0]}' is not a valid output")

            result = function(*args, **kwargs)

            if 'capabilities' in args:
                result['capabilities'] = possibleOutputs

            return result if len(result)>1 else list(result.items())[0][1]
        return wrapper
    return real_decorator


def runInParallel(*fns):
    proc = []
    for fn in fns:

        if len(fn)==1:
            p = Process(target=fn[0])
        else:
            p = Process(target=fn[0], args=fn[1:])
        p.start()
        proc.append(p)
    for p in proc:
        p.join()



