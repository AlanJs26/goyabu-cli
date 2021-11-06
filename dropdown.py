import tty, sys, termios, os
import termtables as tt
import re

bcolors = {
    'header': '\033[95m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'green': '\033[92m',
    'warning': '\033[93m',
    'fail': '\033[91m',
    'end': '\033[0m',
    'bold': '\033[1m',
    'underline': '\033[4m'
}

def c(color, text):
    return bcolors[color] + text + bcolors['end'] 

class HighlightedTable:
    def __init__(self, items, header, highlights, alignment="rc", highlightRange=(1,1)):
        table = tt.to_string(
            items,
            header=header,
            style=tt.styles.rounded,
            alignment=alignment,
        )
        table = table.split('\n')
        table = '\n'.join(table[0:2]+[table[2]]+table[1::2][1:]+table[-1:])
        self.tableLines = table.split('\n')[3:-1]
        self.tableHeader = '\n'.join(table.split('\n')[:3])
        self.tableFooter = table.split('\n')[-1]
        self.highlights = highlights
        self.highlightRange = highlightRange

    def update(self, highlights=None, upOffset=0):
        if(highlights == None): highlights=self.highlights

        highlightPos = -1

        print(self.tableHeader)
        for i, line in enumerate(self.tableLines):
            highlightColor = ''

            for highlight in highlights:
                if highlight[0] == i:
                    highlightPos = highlight[0]
                    highlightColor += ''.join(bcolors[color] for color in highlight[1:])

            if i == highlightPos:
                #  line = re.sub(r"(│.+?│\s+)(.+?)(\s+│.+?│)", r"\1{}\2{}\3".format(highlightColor, bcolors['end']), line)
                f1 = self.highlightRange[0]
                f2 = self.highlightRange[1]
                if bcolors['end'] in line:
                    line = re.sub(r"((.*?│.*?){"+str(f1)+r"})(..\b.+\b\S?)((.*?│.*?){"+str(f2)+r"})", r"\1{}\3\4".format(highlightColor), line)
                else:
                    line = re.sub(r"((.*?│.*?){"+str(f1)+r"})(\b.+\b\S?)((.*?│.*?){"+str(f2)+r"})", r"\1{}\3{}\4".format(highlightColor, bcolors['end']), line)
            print(line)
        print(self.tableFooter)


        self.cursorToBeginning(upOffset)

    def cursorToEnd(self, downOffset=0):
        sys.stdout.write(f"\033[{len(self.tableLines)+4+downOffset}E")

    def cursorToBeginning(self, upOffset=0):
        sys.stdout.write(f"\033[{len(self.tableLines)+4+upOffset}F")
        sys.stdout.write("\r")

    def clear(self):
        sys.stdout.write(f"\033[J")


def multiselectionTable(key: str, table:HighlightedTable, highlightList: list, highlightPos: int, ignoredKeys=[], appendText=""):
    currentPos = highlightList[0][0]
    currentItem = highlightList[0]
    newHighlighList = []

    if highlightPos < 1: 
        highlightPos = 0
        highlightList[0][0] = 0

    if highlightPos >= len(table.tableLines) or ignoredKeys:
        highlightPos = len(table.tableLines)
        highlightList[0][0] = len(table.tableLines)
        if ignoredKeys:
            if ord(key) == 27:
                key=sys.stdin.read(1)
                highlightPos = len(table.tableLines) -(1 if key != 'A' else -1)
                highlightList[0][0] = len(table.tableLines) -(1 if key != 'A' else -1)
                ignoredKeys=[]
            elif ord(key) == 127:
                appendText = appendText[:-1]
            else: 
                appendText+=key
        else:
            ignoredKeys = ['j', 'k', '[', 'q']

    if key == "c" or ord(key) == 32:
        newHighlighList = [item for item in highlightList[1:] if item[0] != currentPos]

        newHighlighList = [currentItem, *newHighlighList]

        wasNotFound = len(newHighlighList) == len(highlightList)
        if wasNotFound == True:
            newHighlighList.append([currentPos, 'fail'])
    else:
        newHighlighList = highlightList

    return newHighlighList, highlightPos, appendText if ignoredKeys else '', ignoredKeys

def interactiveTable(items:list, header:list, alignment="rc", keyCallback=None, clipPos=True, behaviour="single", hintText='Digite: ', staticHighlights=[], highlightRange=(1,1)):
    filedescriptors = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)

    highlightPos = 0
    ignoredKeys = []
    appendText = ''
    #  hintText='Digite: '

    if 'multiSelect' in behaviour:
        keyCallback = multiselectionTable

    if 'WithText' in behaviour:
        ignoredKeys = 'j k [ q'.split(' ')
        clipPos=False
        highlightPos = len(items)

    highlightList = [[highlightPos, 'underline', 'bold']]

    table = HighlightedTable(items, header, highlightList, alignment, highlightRange=highlightRange)
    table.update([*staticHighlights,*highlightList])
    table.cursorToEnd(-1 if 'WithText' in behaviour else 0)

    if 'WithText' in behaviour: 
        sys.stdout.write(f"\n\033[2K{(hintText if appendText or highlightPos==len(items) else '')+appendText}")
        #  sys.stdout.write(f"\033[1F")

    while True:

        try:
            key=sys.stdin.read(1)
        except KeyboardInterrupt:
            print('\n')
            os._exit(0)

        table.cursorToBeginning(0)

        if key not in ignoredKeys:
            if key == 'q':
                os._exit(0)

            if key == '\n':
                break

            if key == 'j':
                highlightPos=highlightPos+1 if highlightPos<len(items)-1 or clipPos==False else highlightPos

            if key == 'k':
                highlightPos=highlightPos-1 if highlightPos>0 or clipPos==False else highlightPos

            if key == '[':
                key=sys.stdin.read(1)
                ignoredKeys = []

                #  if key == 'C': # right
                #  if key == 'D': # left
                if  key == 'A':    # up
                    highlightPos=highlightPos-1 if highlightPos>0            or clipPos==False else highlightPos
                elif key == 'B':  # down
                    highlightPos=highlightPos+1 if highlightPos<len(items)-1 or clipPos==False else highlightPos

        highlightList[0] = [highlightPos, 'underline', 'bold']

        if keyCallback != None:
            highlightList, highlightPos, appendText, ignoredKeys = keyCallback(key, table, highlightList, highlightPos, ignoredKeys, appendText)

        table.update([*staticHighlights,*highlightList], len((appendText).split('\n')) if 'WithText' in behaviour else 0)

        table.cursorToEnd(0)

        if 'WithText' in behaviour: 
            sys.stdout.write(f"\n\033[2K{(hintText if appendText or highlightPos==len(items) else '')+appendText}")
            #  sys.stdout.write(f"\033[1F")


    table.clear()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
    return items[highlightPos] if highlightPos<len(items) else None, highlightList, appendText

if __name__ == "__main__":
    tablelist = [
        ['episodio 1', 'alan'  ],
        ['episodio 2', 'jose'  ],
        ['episodio 2', 'jose'  ],
        ['episodio 2', 'jose'  ],
        ['episodio 2', 'jose'  ],
        ['episodio 3', 'dos'   ],
        ['episodio 4', 'dos'   ],
        ['episodio 5', 'legal'],
    ]

    print("before")
    results = [[],None,None]
    staticHighlights=[[3, 'green']]

    while results[0] != None:
        results = interactiveTable(tablelist, ["Episódios", "Nome"], "rc", behaviour='multiSelectWithText', hintText='Digite: ', staticHighlights=staticHighlights)

        posToRemove = [item[0] for item in results[1][1:]]
        tablelist = [item for i, item in enumerate(tablelist) if i not in posToRemove]
        staticHighlights = [item for item in staticHighlights if item[0] not in posToRemove]

    print(results)
    os._exit(0)


    if results[-1][len('Digite: '):] != 'delete':
        posToRemove = [item[0] for item in results[1][1:]]
        newTablelist = [item for i, item in enumerate(tablelist) if i not in posToRemove]


        results = interactiveTable(newTablelist, ["Episódios", "Nome"], "rc",  behaviour='multiSelect')
        posToRemove = [item[0] for item in results[1][1:]]
        newTablelist = [item for i, item in enumerate(newTablelist) if i not in posToRemove]
        results = interactiveTable(newTablelist, ["Episódios", "Nome"], "rc",  behaviour='single')
        print(newTablelist)

    print("after")


#  termios.tcsetattr(sys.stdin, termios.TCSADRAIN,filedescriptors)
    

