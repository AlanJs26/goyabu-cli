import sys, os
import re
import termtables as tt
from math import floor

isWindows = sys.platform == 'win32'

filedescriptors = None

if not isWindows:
    import tty, termios
else:
    from msvcrt import getch

bcolors = {
    'header': '\033[95m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'green': '\033[92m',
    'warning': '\033[93m',
    'grey': '\033[38;5;243m',
    'fail': '\033[91m',
    'end': '\033[0m',
    'bold': '\033[1m',
    'underline': '\033[4m'
}

def c(color, text):
    return bcolors[color] + text + bcolors['end'] 

def readchr(readNum=1):
    global filedescriptors
    if isWindows:
        character = []
        for _ in range(readNum):
            character.append(getch())
        remapList = { 
            b'\xe0': b'[',
            b'H': b'A',
            b'P': b'B',
            b'\x08': b'\b',
            b'\r': b'\n',
        }
        
        # for accented characters
        if character == b'\xc3':
            character.append(getch())

        for i in range(len(character)):
            if character[i] in remapList:
                character[i] = remapList[character[i]]
        # print(character)

        if type(character) == str:
            return character
        else:
            newCharacter = ''
            for ch in character:
                newCharacter += ch.decode()
            return newCharacter
            # return character.decode()

    if filedescriptors == None:
        filedescriptors = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)
        
    return sys.stdin.read(readNum)


def endRawmode():
    if isWindows:
        return
    global filedescriptors

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
    filedescriptors=None


class HighlightedTable:
    def __init__(self, items, header, highlights, alignment="rc", highlightRange=(1,1), maxListSize=5):
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
        self.maxListSize = maxListSize

    def update(self, highlights=None, upOffset=0, scrollAmount=0):
        if(highlights == None): highlights=self.highlights

        if self.maxListSize > len(self.tableLines):
            self.maxListSize = len(self.tableLines)

        maxScrollAmount = len(self.tableLines)-self.maxListSize
        if scrollAmount > maxScrollAmount:
            scrollAmount = maxScrollAmount


        highlightPos = -1

        scrollSlice = slice(scrollAmount, scrollAmount+self.maxListSize)

        if scrollAmount > 0:
            lastOccurrence = self.tableHeader.rfind('┼')
            print(self.tableHeader[:lastOccurrence-1]+' ↑ '+self.tableHeader[lastOccurrence+2:])
        else:
            print(self.tableHeader)

        for index, line in enumerate(self.tableLines[scrollSlice]):
            i = index+scrollAmount
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

        if scrollAmount+self.maxListSize < len(self.tableLines):
            lastOccurrence = self.tableFooter.rfind('┴')
            print(self.tableFooter[:lastOccurrence-1]+' ↓ '+self.tableFooter[lastOccurrence+2:])
        else:
            print(self.tableFooter)



        self.cursorToBeginning(0)

    def cursorToEnd(self, downOffset=0):
        sys.stdout.write(f"\033[{self.maxListSize+4+downOffset}E")

    def cursorToBeginning(self, upOffset=0):
        sys.stdout.write(f"\033[{self.maxListSize+4+upOffset}F")
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
            if ord(key) == 9:
                highlightPos = len(table.tableLines) -1
                highlightList[0][0] = len(table.tableLines) -1
                ignoredKeys=[]
            elif (key == '[' if isWindows else ord(key) == 27):
                key=readchr(1) if isWindows else readchr(2) 
                if key == '[A' or key == 'A':
                    highlightPos = len(table.tableLines) -1
                    highlightList[0][0] = len(table.tableLines) -1
                    ignoredKeys=[]
                key = key[0]
            elif ord(key) == 127 or key == '\b':
                appendText = appendText[:-1]
            else: 
                appendText+=key
        else:
            ignoredKeys = ['j', 'k', '[', 'q']

    if key == "c" or ord(key) == 32 or key == ' ':
        newHighlighList = [item for item in highlightList[1:] if item[0] != currentPos]

        newHighlighList = [currentItem, *newHighlighList]

        wasNotFound = len(newHighlighList) == len(highlightList)
        if wasNotFound == True:
            newHighlighList.append([currentPos, 'fail'])
    else:
        newHighlighList = highlightList

    return newHighlighList, highlightPos, appendText if ignoredKeys else '', ignoredKeys

def interactiveTable(items:list, header:list, alignment="rc", keyCallback=None, clipPos=True, behaviour="single", hintText='Digite: ', maxListSize=5,  staticHighlights=[], highlightRange=(1,1)):
    if len(items) == 0:
        return (None,None,'')


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

    table = HighlightedTable(items, header, highlightList, alignment, highlightRange=highlightRange, maxListSize=maxListSize)
    table.update([*staticHighlights,*highlightList], scrollAmount=highlightPos)
    #  table.cursorToEnd(-1 if 'WithText' in behaviour else 0)
    table.cursorToEnd(0)

    if 'WithText' in behaviour: 
        sys.stdout.write(f"\n\033[2K{(hintText if appendText or highlightPos==len(items) else '')+appendText}")
        #  sys.stdout.write(f"\033[1F")

    while True:

        try:
            key=readchr()
            # print(key)
            # continue
        except KeyboardInterrupt:
            print('\n')
            os._exit(0)

        table.cursorToBeginning(1 if 'WithText' in behaviour else 0)
        #  table.cursorToBeginning(0)

        if key not in ignoredKeys:
            if key == 'q':
                os._exit(0)

            if key == '\n' or key == '\r':
                break

            if key == 'j':
                highlightPos=highlightPos+1 if highlightPos<len(items)-1 or clipPos==False else highlightPos

            if key == 'k' or key == '\t':
                highlightPos=highlightPos-1 if highlightPos>0 or clipPos==False else highlightPos

            if key == '[':
                key=readchr()
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

        table.update([*staticHighlights,*highlightList], len((appendText).split('\n')) if 'WithText' in behaviour else 0, scrollAmount=highlightPos-floor(maxListSize/2) if highlightPos>maxListSize/2 else 0)

        if 'WithText' in behaviour: 
            table.cursorToEnd(0)
            #  sys.stdout.write(f"\033[1E")
            #  sys.stdout.write(f"\033[K")
            #  sys.stdout.write(f"\033[1F")

            sys.stdout.write(f"\n\033[2K{(hintText if appendText or highlightPos==len(items) else '')+appendText}")
            #  sys.stdout.write(f"\033[1F")
        else:
            table.cursorToEnd(0)


    table.clear()
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
    endRawmode()
    return items[highlightPos] if highlightPos<len(items) else None, highlightList, appendText

if __name__ == "__main__":
    tablelist = [
        ['episodio 1', 'episodio 1', 'um'     ],
        ['episodio 2', 'episodio 2', 'dois'   ],
        ['episodio 3', 'episodio 3', 'tres'   ],
        ['episodio 4', 'episodio 4', 'quatro' ],
        ['episodio 4', 'episodio 4', 'quatro' ],
        ['episodio 5', 'episodio 5', 'cinco'  ],
        ['episodio 6', 'episodio 6', 'seis'   ],
        ['episodio 7', 'episodio 7', 'sete'   ],
        ['episodio 8', 'episodio 8', 'oito'   ],
        ['episodio 5', 'episodio 5', 'cinco'  ],
        ['episodio 6', 'episodio 6', 'seis'   ],
        ['episodio 7', 'episodio 7', 'sete'   ],
        ['episodio 8', 'episodio 8', 'oito'   ],
    ]

    print("before")
    results = [[],None,None]
    staticHighlights=[[3, 'green']]

    # while True:
    #     key = readchr(1)
    #     print(key)
    #     if key == 'q':
    #         break

    # while results[0] != None:
    results = interactiveTable(
        tablelist,
        ['' ,"Episódios", "Nome"],
        "rcc",
        behaviour='multiSelectWithText',
        maxListSize=7,
        staticHighlights=staticHighlights,
        highlightRange=(2,2)
    )
    print(results)

    # posToRemove = [item[0] for item in results[1][1:]]
    # tablelist = [item for i, item in enumerate(tablelist) if i not in posToRemove]
    # staticHighlights = [item for item in staticHighlights if item[0] not in posToRemove]
    #
    # print(results)


    # if results[-1][len('Digite: '):] != 'delete':
    #     posToRemove = [item[0] for item in results[1][1:]]
    #     newTablelist = [item for i, item in enumerate(tablelist) if i not in posToRemove]
    #
    #
    #     results = interactiveTable(newTablelist, ["Episódios", "Nome"], "rc",  behaviour='multiSelect')
    #     posToRemove = [item[0] for item in results[1][1:]]
    #     newTablelist = [item for i, item in enumerate(newTablelist) if i not in posToRemove]
    #     results = interactiveTable(newTablelist, ["Episódios", "Nome"], "rc",  behaviour='single')
    #     print(newTablelist)

    #  print("after")


#  termios.tcsetattr(sys.stdin, termios.TCSADRAIN,filedescriptors)
    

