from functools import wraps
from multiprocessing import Process
from os import get_terminal_size, path

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

def dir_path(string):
    if string == '': return ''
    new_string = path.expanduser(string)
    if path.isdir(new_string):
        return new_string
    else:
        raise NotADirectoryError(string)

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

translation = {
    'last_sessions': {
        'en': 'Last Sessions',
        'pt': 'Sess??es Anteriores'
    },
    'date': {
        'en': 'Date',
        'pt': 'Data'
    },
    'hintText': {
        'en': 'Anime Name[1]: ',
        'pt': 'Nome do Anime[1]: '
    },
    'inputText': {
        'en': 'Anime Name',
        'pt': 'Nome do Anime:'
    },
    'invalidName': {
        'en': 'Please enter a valid name to continue',
        'pt': 'Insira um nome v??lido para continuar'
    },
    'animeNotFound': {
        'en': '\nNo anime with the name "{}" was found. Try another name.',
        'pt': '\nNenhum anime com o nome "{}" foi encontrado. Tente outro nome.'
    },
    'episodes': {
        'en': 'Episodes',
        'pt': 'Epis??dios'
    },
    'sliceHelp': {
        'en': '''
        n - single episode
        n:n - range of episodes
        all - all episodes
        ''',
        'pt': '''
        n - ??nico epis??dio
        n:n - intervalo de epis??dios
        todos - todos os epis??dios
        '''
    },
    'sliceHint': {
        'en': 'Episodes[all]:',
        'pt': 'Epis??dios para assistir [todos]: ' 
    },
    'savingIn': {
        'en': 'Saving in "{}"',
        'pt': 'Salvando em "{}"'
    },
    'listUpdated': {
        'en': 'local list updated',
        'pt': 'lista de epis??dios sincronizada'
    },
    'listUpdating': {
        'en': 'synching the local list',
        'pt': 'sincronizando a lista de epis??dios'
    },
    'mpvNotFound': {
        'en': 'MPV is not installed, please specify an alternative player or serve the file over network using the "--player none" argument',
        'pt': 'O MPV n??o est?? instalado, especifique um player alternativo ou transmita o arquivo pela rede local usando o argumento "--player none" '
    },
    'complete': {
        'en': 'Complete',
        'pt': 'Completo'
    },
    'daysAgo': {
        'en': 'days ago',
        'pt': 'dias atr??s'
    },
}

