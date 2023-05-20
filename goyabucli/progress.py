from contextlib import contextmanager
from sys import stdout
from os import get_terminal_size
from typing import overload

class ProgressBar():
    """Simple progress bar that works on windows"""
    @overload
    def __init__(self, total:int=0, postfix:list[str]=[], left_delimiter='|', right_delimiter='|', leave=True):
        pass

    @overload
    def __init__(self, total:int, postfix:str='', left_delimiter='|', right_delimiter='|', leave=True):
        pass

    def __init__(self, total:int=0, postfix:str|list[str]='', left_delimiter='|', right_delimiter='|', leave=True):
        self.total = total
        self.leave = leave
        self.closed = False

        if isinstance(postfix, str):
            self.postfix = ', '+postfix
        else:
            self.postfix = [', '+pfx for pfx in postfix]
            self.total = len(postfix)-1

        self.count = 0

        self.left_delimiter = left_delimiter
        self.right_delimiter = right_delimiter

        self._refresh_width()

        self._show()

    def _refresh_width(self):
        if isinstance(self.postfix, str):
            self.width = get_terminal_size().columns - len(self.left_delimiter+self.postfix+self.right_delimiter)
        else:
            self.width = get_terminal_size().columns - len(self.left_delimiter+self.postfix[self.count]+self.right_delimiter)

    def _show(self):
        self._refresh_width()
        num_progress = f' {self.count}/{self.total}'
        width = self.width-len(num_progress)

        count = round((self.count/self.total)*width)



        print(self.left_delimiter, end='')

        print('#'*count, end='')
        print(' '*(width-count), end='')

        print(self.right_delimiter, num_progress, end='', sep='')

        if self.postfix:
            if isinstance(self.postfix, str):
                print(self.postfix, end='')
            else:
                print(self.postfix[self.count], end='')

        print('', end='\r')

    def close(self):
        if not self.leave and not self.closed:
            stdout.write("\r\033[K")
            self.closed = True

    def update(self, num:int):
        self.count+=num

        if self.count >= self.total:
            self.count = self.total

        self._show()

@contextmanager
def progress(total:int=0, postfix:str|list[str]='', leave=True):
    bar = ProgressBar(total, postfix, leave=leave)

    yield bar

    bar.close()



if __name__ == '__main__':
    from time import sleep
    with progress(postfix=[], leave=False) as bar:
        for i in range(5):
            sleep(2)
            bar.update(1)
    print('jose')
        
