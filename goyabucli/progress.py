from contextlib import contextmanager
from sys import stdout
from os import get_terminal_size

class ProgressBar():
    """Simple progress bar that works on windows"""
    def __init__(self, total:int, postfix='', left_delimiter='|', right_delimiter='|', leave=True):
        self.total = total
        self.leave = leave
        self.postfix = ', '+postfix
        self.count = 0

        self.left_delimiter = left_delimiter
        self.right_delimiter = right_delimiter

        self.width = get_terminal_size().columns - len(self.left_delimiter+self.postfix+self.right_delimiter)

        self._show()

    def _show(self):
        num_progress = f' {self.count}/{self.total}'
        width = self.width-len(num_progress)

        count = round((self.count/self.total)*width)



        print(self.left_delimiter, end='')

        print('#'*count, end='')
        print(' '*(width-count), end='')

        print(self.right_delimiter, num_progress, end='', sep='')

        if self.postfix:
            print(self.postfix, end='')

        print('', end='\r')

    def close(self):
        if not self.leave:
            stdout.write("\r\033[K")

    def update(self, num:int):
        self.count+=num

        if self.count >= self.total:
            self.count = self.total

        self._show()

@contextmanager
def progress(total:int, postfix='', leave=True):
    bar = ProgressBar(total, postfix, leave=leave)

    yield bar

    bar.close()



if __name__ == '__main__':
    from time import sleep
    with progress(5, 'alan', leave=False) as bar:
        for i in range(5):
            sleep(0.5)
            bar.update(1)
    print('jose')
        
