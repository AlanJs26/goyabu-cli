from functools import wraps
from multiprocessing import Process

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


def infoDecorator(outputs):
    def real_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            difference = list(set(args).difference(outputs))
            if len(difference) > 1:
                raise SystemExit(f"'{' and '.join(difference)}' are not valid outputs")
            elif len(difference):
                raise SystemExit(f"'{difference[0]}' is not a valid output")

            result = function(*args, **kwargs)

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