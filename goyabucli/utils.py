from functools import wraps
from multiprocessing import Process
from os import get_terminal_size
import re



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

search_buffer = {}

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def animeTitle2Id(title:str):
    remove_patterns = [r'\(tv\)', r'\(dub\)']

    for pattern in remove_patterns:
        title = re.sub(pattern, '', title)

    return title

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



