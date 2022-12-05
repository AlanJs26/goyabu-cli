import sys, os
import re
import termtables as tt
from math import floor
from functools import reduce
from typing import TypedDict,List,Callable,Optional,cast,Union,Dict
from utils import nameTrunc

from copy import deepcopy

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

class THighlight(TypedDict):
    pos: int
    color: str


class HighlightedTable:
    def __init__(self, items:list, header:list, highlights:List[THighlight], alignment="rc", highlightRange=(1,1), maxListSize=5, flexColumn=0, width=0):
        newItems = deepcopy(items)
        if width>0:
            if flexColumn < 0 or flexColumn >= len(header):
                raise Exception('Invalid flexColumn: must be a valid column index')
            for item in newItems:
                linelength = reduce(lambda p,n:len(n)+p, item, 0)
                item[flexColumn] = nameTrunc(item[flexColumn], linelength+18)
        table = tt.to_string(
            newItems,
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

    def update(self, highlights:List[THighlight]=[], upOffset=0, scrollAmount=0):
        if(not highlights): highlights=self.highlights

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
                if highlight['pos'] == i:
                    highlightPos = highlight['pos']
                    highlightColor += ''.join(bcolors[color] for color in highlight['color'].split(','))

            if i == highlightPos:
                #  line = re.sub(r"(│.+?│\s+)(.+?)(\s+│.+?│)", r"\1{}\2{}\3".format(highlightColor, bcolors['end']), line)
                f1 = self.highlightRange[0]
                f2 = self.highlightRange[1]
                # if bcolors['end'] in line:
                #     line = re.sub(r"((.*?│.*?){"+str(f1)+r"})(..\b.+\b\S?)((.*?│.*?){"+str(f2)+r"})", r"\1{}\3\4".format(highlightColor), line)
                # else:
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

class TKeyCallbackReturn(TypedDict):
    highlights: List[THighlight]
    pos: int
    placeholder: str
    text: str
    ignoredKeys: List[str]

TKeyCallback = Callable[[str, HighlightedTable, List[THighlight], int, list, str], TKeyCallbackReturn]

def _multiselectionTable(key: str, table:HighlightedTable, highlightList: List[THighlight], highlightPos: int, ignoredKeys=[], inputText="") -> TKeyCallbackReturn:
    currentHightlight = highlightList[0]

    if highlightPos < 1: 
        highlightPos = 0
        currentHightlight['pos'] = 0

    if highlightPos >= len(table.tableLines) or ignoredKeys:
        highlightPos = len(table.tableLines)
        currentHightlight['pos'] = len(table.tableLines)
        if ignoredKeys:
            if ord(key) == 9:
                highlightPos = len(table.tableLines) -1
                currentHightlight['pos'] = len(table.tableLines) -1
                ignoredKeys=[]
            elif (key == '[' if isWindows else ord(key) == 27):
                key=readchr(1) if isWindows else readchr(2) 
                if key == '[A' or key == 'A':
                    highlightPos = len(table.tableLines) -1
                    currentHightlight['pos'] = len(table.tableLines) -1
                    ignoredKeys=[]
                key = key[0]
            elif ord(key) == 127 or key == '\b':
                inputText = inputText[:-1]
            else: 
                inputText+=key
        else:
            ignoredKeys = ['j', 'k', '[', 'q']

    newHighlighList = []
    if highlightPos < len(table.tableLines) and (key == "c" or ord(key) == 32 or key == ' '):
        newHighlighList = [item for item in highlightList[1:] if item['pos'] != currentHightlight['pos']]

        newHighlighList = [currentHightlight, *newHighlighList]

        wasNotFound = len(newHighlighList) == len(highlightList)
        if wasNotFound == True:
            newHighlighList.append({
                'pos': currentHightlight['pos'],
                'color': 'fail'
            })
    else:
        newHighlighList = highlightList

    return {
        'highlights': newHighlighList,
        'pos': highlightPos,
        'text': inputText,
        'placeholder': inputText if ignoredKeys else '',
        'ignoredKeys': ignoredKeys
    }

multiselectionTable:TKeyCallback = cast(TKeyCallback,_multiselectionTable)

class TableResults(TypedDict):
    selectedPos: Union[int,None]
    selectedItem: Union[list,None]
    text: str
    items: Union[Dict[int, list],None]

def interactiveTable(
    items:List[list], header:list, alignment="rc", keyCallback:Optional[TKeyCallback]=None,
        clipPos=True, behaviour="single", hintText='Digite: ',
        maxListSize=5, staticHighlights:List[THighlight]=[], highlightRange=(1,1),
        width=0, flexColumn=0) -> TableResults:

    if len(header) <= 1:
        raise Exception('the number of columns must be greater than 1')
    if not items:
        return {
            'selectedPos': None,
            'selectedItem': None,
            'text': '',
            'items': None
        }

    highlightPos = 0
    ignoredKeys = []
    inputText = ''

    def selectedStyle(pos:int) -> THighlight:
        return {
            'pos': pos,
            'color': 'underline'
        }

    if 'multiSelect' in behaviour:
        keyCallback = multiselectionTable

    if 'WithText' in behaviour:
        ignoredKeys = ['j', 'k', '[', 'q'] # ignore default event while in text input
        clipPos=False # allow reach text position
        highlightPos = len(items) # last position (text input position)

    highlights : List[THighlight] = [selectedStyle(highlightPos)]

    table = HighlightedTable(items, header, highlights, alignment, highlightRange=highlightRange, maxListSize=maxListSize, width=width,flexColumn=flexColumn)
    table.update([*staticHighlights,*highlights], scrollAmount=highlightPos)
    #  table.cursorToEnd(-1 if 'WithText' in behaviour else 0)
    table.cursorToEnd(0)

    if 'WithText' in behaviour: 
        sys.stdout.write(f"\n\033[2K{(hintText if inputText or highlightPos==len(items) else '')+inputText}")
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

        highlights[0] = selectedStyle(highlightPos) 

        if keyCallback is not None and isinstance(key,str):
            results = keyCallback(key, table, highlights, highlightPos, ignoredKeys, inputText)
            highlights = results['highlights']
            highlightPos = results['pos']
            inputText = results['placeholder']
            ignoredKeys = results['ignoredKeys']
            inputText = results['text']
            # highlights, highlightPos, placeholder, ignoredKeys = keyCallback(key, table, highlights, highlightPos, ignoredKeys, placeholder)

        table.update(
            [*staticHighlights,*highlights],
            len(inputText.split('\n')) if 'WithText' in behaviour else 0,
            scrollAmount=highlightPos-floor(maxListSize/2) if highlightPos>maxListSize/2 else 0
        )

        if 'WithText' in behaviour: 
            table.cursorToEnd(0)
            #  sys.stdout.write(f"\033[1E")
            #  sys.stdout.write(f"\033[K")
            #  sys.stdout.write(f"\033[1F")

            sys.stdout.write(f"\n\033[2K{(hintText if inputText or highlightPos==len(items) else '')+inputText}")
            #  sys.stdout.write(f"\033[1F")
        else:
            table.cursorToEnd(0)


    table.clear()
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
    endRawmode()

    print(highlights)

    selectedItems = {item['pos']: items[item['pos']] for item in highlights if item['color'] == 'fail'}
    return {
        'selectedPos': highlightPos if highlightPos < len(items) else None,
        'selectedItem': items[highlightPos] if highlightPos<len(items) else None,
        'items': selectedItems if selectedItems else None,
        'text': inputText
    }

if __name__ == "__main__":
    tablelist = [
        ['episodio 1', 'episodio 0',  'um'     ],
        ['episodio 2', 'episodio 1',  'dois'   ],
        ['episodio 3', 'episodio 2',  'tres'   ],
        ['episodio 4', 'episodio 3',  'quatro' ],
        ['episodio 4', 'episodio 4',  'quatro' ],
        ['episodio 5', 'episodio 5',  'cinco'  ],
        ['episodio 6', 'episodio 6',  'seis'   ],
        ['episodio 7', 'episodio 7',  'sete'   ],
        ['episodio 8', 'episodio 8',  'oito'   ],
        ['episodio 5', 'episodio 9',  'nove'   ],
        ['episodio 6', 'episodio 10', 'dez'    ],
        ['episodio 7', 'episodio 11', 'onze'   ],
        ['episodio 8', 'episodio 12', 'doze'   ],
    ]

    print("before")
    staticHighlights:List[THighlight]=[{'pos': 3, 'color': 'green'}]

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
        behaviour='multiSelect',
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
    

