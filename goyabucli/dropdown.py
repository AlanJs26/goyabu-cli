import sys, os
import re
from copy import deepcopy
import termtables as tt
from math import floor
from functools import reduce
from typing import List,Callable,Optional,cast,Union,Dict,Tuple
from dataclasses import dataclass
from goyabucli.utils import nameTrunc

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

class Cursor:
    def __init__(self):
        pass

    @staticmethod
    def down(amount=0):
        sys.stdout.write(f"\033[{amount}E")

    @staticmethod
    def startLine():
        sys.stdout.write("\r")

    @staticmethod
    def up(amount=0):
        sys.stdout.write(f"\033[{amount}F")

    @staticmethod
    def eraseLine():
        sys.stdout.write(f"\033[2K")

    @staticmethod
    def clearForward():
        sys.stdout.write(f"\033[J")

@dataclass
class Highlight:
    pos: int
    color: str


class HighlightedTable:
    def __init__(self, items:list, header:list, highlights:List[Highlight], alignment="rc", highlightRange=(1,1), maxListSize=5, flexColumn=0, width=0, message=''):
        self.highlightRange=highlightRange
        self.maxListSize=maxListSize
        self.highlights=[]

        self.update(items,header,highlights,alignment,highlightRange,maxListSize,flexColumn,width, message)

    def update(self,
               items:List[List[str]],
               header:Optional[List[str]]=None,
               highlights:Optional[List[Highlight]]=None,
               alignment:Optional[str]=None,
               highlightRange:Optional[Tuple[int, int]]=None,
               maxListSize:Optional[int]=None,
               flexColumn:Optional[int]=None,
               width:Optional[int]=None,
               message:Optional[str]=None):

        self.real_items = items
        self.items = deepcopy(items)
        if flexColumn is not None:
            self.flexColumn = flexColumn
        if alignment is not None:
            self.alignment = alignment
        if header is not None:
            self.header = header
        if width is not None:
            self.width = width
        if message is not None:
            self.message = message
        if highlightRange is not None:
            self.highlightRange = highlightRange
        if highlights is not None:
            self.highlights = highlights
        if maxListSize is not None:
            self.maxListSize = maxListSize


        if self.width>0:
            if self.flexColumn < 0 or self.flexColumn >= len(self.header):
                raise Exception('Invalid self.flexColumn: must be a valid column index')
            for item in self.items:
                linelength = reduce(lambda p,n:len(n)+p, item, 0)
                item[self.flexColumn] = nameTrunc(item[self.flexColumn], linelength+18)
        table = tt.to_string(
            self.items,
            header=self.header,
            style=tt.styles.rounded,
            alignment=self.alignment,
        )
        table = table.split('\n')
        table = '\n'.join(table[0:2]+[table[2]]+table[1::2][1:]+table[-1:])
        self.tableLines = table.split('\n')[3:-1]
        self.tableHeader = '\n'.join(table.split('\n')[:3])
        self.tableFooter = table.split('\n')[-1]


    def display(self, highlights:List[Highlight]=[], upOffset=0, scrollAmount=0):
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
                if highlight.pos == i:
                    highlightPos = highlight.pos
                    highlightColor += ''.join(bcolors[color] for color in highlight.color.split(','))

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

        if self.message:
            Cursor.down(2)
            message = self.message.split('\n') 

            for item in message:
                sys.stdout.write(f"\033[{len(self.tableLines[0])+2}C")
                print(item)
            Cursor.up(len(message)+2)

    def cursorToEnd(self, downOffset=0):
        Cursor.down(self.maxListSize+4+downOffset)

    def cursorToBeginning(self, upOffset=0):
        Cursor.up(self.maxListSize+4+upOffset)
        Cursor.startLine()

@dataclass
class KeyCallbackReturn:
    highlights: List[Highlight]
    pos: int
    placeholder: str
    text: str
    ignoredKeys: List[str]

KeyCallback = Callable[[str, HighlightedTable, List[Highlight], int, list, str], KeyCallbackReturn]

def _multiselectionTable(key: str, table:HighlightedTable, highlightList: List[Highlight], highlightPos: int, ignoredKeys=[], inputText="") -> KeyCallbackReturn:
    currentHighlight = highlightList[0]

    if highlightPos < 1: 
        highlightPos = 0
        currentHighlight.pos = 0

    if highlightPos >= len(table.tableLines) or ignoredKeys:
        highlightPos = len(table.tableLines)
        currentHighlight.pos = len(table.tableLines)
        if ignoredKeys:
            if ord(key) == 9:
                highlightPos = len(table.tableLines) -1
                currentHighlight.pos = len(table.tableLines) -1
                ignoredKeys=[]
            elif (key == '[' if isWindows else ord(key) == 27):
                key=readchr(1) if isWindows else readchr(2) 
                if key == '[A' or key == 'A':
                    highlightPos = len(table.tableLines) -1
                    currentHighlight.pos = len(table.tableLines) -1
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
        newHighlighList = [item for item in highlightList[1:] if item.pos != currentHighlight.pos]

        newHighlighList = [currentHighlight, *newHighlighList]

        wasNotFound = len(newHighlighList) == len(highlightList)
        if wasNotFound == True:
            newHighlighList.append(Highlight(pos=currentHighlight.pos, color='fail'))
    else:
        newHighlighList = highlightList

    return KeyCallbackReturn(
        highlights=newHighlighList,
        pos=highlightPos,
        text=inputText,
        placeholder=inputText,
        ignoredKeys=ignoredKeys
    )


def _singleselectionTable(key: str, table:HighlightedTable, highlightList: List[Highlight], highlightPos: int, ignoredKeys=[], inputText="") -> KeyCallbackReturn:
    currentHighlight = highlightList[0]

    if highlightPos < 1: 
        highlightPos = 0
        currentHighlight.pos = 0

    if highlightPos >= len(table.tableLines) or ignoredKeys:
        highlightPos = len(table.tableLines)
        currentHighlight.pos = len(table.tableLines)
        if ignoredKeys:
            if ord(key) == 9:
                highlightPos = len(table.tableLines) -1
                currentHighlight.pos = len(table.tableLines) -1
                ignoredKeys=[]
            elif (key == '[' if isWindows else ord(key) == 27):
                key=readchr(1) if isWindows else readchr(2) 
                if key == '[A' or key == 'A':
                    highlightPos = len(table.tableLines) -1
                    currentHighlight.pos = len(table.tableLines) -1
                    ignoredKeys=[]
                key = key[0]
            elif ord(key) == 127 or key == '\b':
                inputText = inputText[:-1]
            else: 
                inputText+=key
        else:
            ignoredKeys = ['j', 'k', '[', 'q']

    return KeyCallbackReturn(
        highlights=highlightList,
        pos=highlightPos,
        text=inputText,
        placeholder=inputText,
        ignoredKeys=ignoredKeys
    )

multiselectionTable:KeyCallback = cast(KeyCallback,_multiselectionTable)
singleselectionTable:KeyCallback = cast(KeyCallback,_singleselectionTable)

@dataclass
class TableResults:
    selectedPos: Union[int,None]
    realSelectedPos: Union[int,None]
    selectedItem: Union[list,None]
    text: str
    items: Union[Dict[int, list],None]


FilterCallback = Callable[[str,List[List[str]], HighlightedTable], None]


def interactiveTable(
    items:List[List[str]], header:list, alignment="rc", keyCallback:Optional[KeyCallback]=singleselectionTable,
        clipPos=True, behaviour="single", hintText='Digite: ',
        maxListSize=5, staticHighlights:List[Highlight]=[], highlightRange=(1,1),
    width=0, flexColumn=0, filters:List[str]=[], filter_callback:Optional[FilterCallback]=None) -> TableResults:

    if len(header) <= 1:
        raise Exception('the number of columns must be greater than 1')
    if not items:
        return TableResults(
            realSelectedPos=None,
            selectedPos=None,
            selectedItem=None,
            text='',
            items=None
        )

    highlightPos = 0
    ignoredKeys = []
    inputText = ''

    currentFilterIndex=0

    if 'multiSelect' in behaviour:
        keyCallback = multiselectionTable
    elif 'single' in behaviour:
        keyCallback = singleselectionTable

    def selectedStyle(pos:int) -> Highlight:
        return Highlight(pos=pos, color='underline')

    highlights : List[Highlight] = [selectedStyle(highlightPos)]

    table = HighlightedTable(items, header, highlights, alignment, highlightRange=highlightRange, maxListSize=maxListSize, width=width,flexColumn=flexColumn)

    if 'WithText' in behaviour:
        ignoredKeys = ['j', 'k','l','h', '[', 'q'] # ignore default event while in text input
        clipPos=False # allow reach text position
        highlightPos = len(table.items) # last position (text input position)

    table.display([*staticHighlights,*highlights], scrollAmount=highlightPos)
    table.cursorToEnd(0)

    if 'WithText' in behaviour: 
        sys.stdout.write("\n")
        Cursor.eraseLine()
        sys.stdout.write(f"{(hintText if inputText or highlightPos==len(table.items) else '')+inputText}")

    shouldQuit = False

    def switchFilter(direction='next'):
        nonlocal currentFilterIndex
        nonlocal highlightPos
        nonlocal table
        nonlocal items
        nonlocal filters

        if len(filters) and filter_callback is not None:
            if direction == 'next':
                currentFilterIndex = (currentFilterIndex+1)%len(filters)
            else:
                currentFilterIndex = (currentFilterIndex-1)%len(filters)

            selectedItem = table.real_items[highlightPos] if highlightPos<len(table.items) else None
            filter_callback(filters[currentFilterIndex], items, table)

            realSelectedPos = table.real_items.index(selectedItem) if selectedItem in table.items else None

            if realSelectedPos is not None:
                highlightPos = realSelectedPos
            elif highlightPos >= len(table.items):
                highlightPos=len(table.items)-1

    while True:
        try:
            key=readchr()
        except KeyboardInterrupt:
            shouldQuit = True
            break

        table.cursorToBeginning(1 if 'WithText' in behaviour else 0)

        if key not in ignoredKeys:
            if key == 'q':
                shouldQuit = True
                break

            if key == '\n' or key == '\r':
                break

            elif key == 'j':
                highlightPos=highlightPos+1 if highlightPos<len(table.items)-1 or clipPos==False else highlightPos

            elif key == 'k' or key == '\t':
                highlightPos=highlightPos-1 if highlightPos>0 or clipPos==False else highlightPos

            elif key == 'l':
                switchFilter('next')

            elif key == 'h' and len(filters) and filter_callback is not None:
                switchFilter('previous')

            elif key == '[':
                key=readchr()
                ignoredKeys = []

                if key == 'C' and len(filters) and filter_callback is not None: # right
                    switchFilter('next')

                elif key == 'D' and len(filters) and filter_callback is not None: # left
                    switchFilter('previous')

                elif  key == 'A':    # up
                    highlightPos=highlightPos-1 if highlightPos>0            or clipPos==False else highlightPos
                elif key == 'B':  # down
                    highlightPos=highlightPos+1 if highlightPos<len(table.items)-1 or clipPos==False else highlightPos

        highlights[0] = selectedStyle(highlightPos) 

        if keyCallback is not None and isinstance(key,str):
            results = keyCallback(key, table, highlights, highlightPos, ignoredKeys, inputText)
            highlights = results.highlights
            highlightPos = results.pos
            inputText = results.placeholder
            ignoredKeys = results.ignoredKeys
            inputText = results.text
            # highlights, highlightPos, placeholder, ignoredKeys = keyCallback(key, table, highlights, highlightPos, ignoredKeys, placeholder)

        table.display(
            [*staticHighlights,*highlights],
            len(inputText.split('\n')) if 'WithText' in behaviour else 0,
            scrollAmount=highlightPos-floor(maxListSize/2) if highlightPos>maxListSize/2 else 0
        )

        if 'WithText' in behaviour: 
            table.cursorToEnd(0)

            sys.stdout.write(f"\n\033[2K{(hintText if inputText or highlightPos==len(table.items) else '')+inputText}")
        else:
            table.cursorToEnd(0)


    Cursor.clearForward()
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
    endRawmode()

    if shouldQuit:
        os._exit(0)

    selectedItems = {items.index(table.real_items[item.pos]): table.real_items[item.pos] for item in highlights if item.color == 'fail'}
    selectedItem = table.real_items[highlightPos] if highlightPos<len(table.items) else None

    return TableResults(
        selectedPos     = highlightPos if highlightPos < len(table.items) else None,
        selectedItem    = selectedItem,
        items           = selectedItems if selectedItems else None,
        realSelectedPos = items.index(selectedItem) if selectedItem else None,
        text            = inputText
    )

if __name__ == "__main__":
    tablelist = [
        ['episodio 1', 'ichi',  'um'     ],
        ['episodio 2', 'ni',  'dois'   ],
        ['episodio 3', 'san',  'tres'   ],
        ['episodio 4', 'yon',  'quatro' ],
        ['episodio 5', 'go',  'quatro' ],
        ['episodio 6', 'roku',  'cinco'  ],
        ['episodio 7', 'nana',  'seis'   ],
        ['episodio 8', 'hachi',  'sete'   ],
        ['episodio 9', 'kyuu',  'oito'   ],
        ['episodio 10', 'jyuu',  'nove'   ],
        ['episodio 11', 'jyuu ichi', 'dez'    ],
        ['episodio 12', 'jyuu ni', 'onze'   ],
        ['episodio 13', 'jyuu san', 'doze'   ],
    ]

    print("before")
    staticHighlights:List[Highlight]=[Highlight(pos=3, color='green')]

    # while True:
    #     key = readchr(1)
    #     print(key)
    #     if key == 'q':
    #         break


    def myfilter(filter_name:str, items:List[List[str]], table:HighlightedTable):
        Cursor.clearForward()
        if filter_name == 'half':
            table.update(list(filter(lambda x:int(x[0].split(' ')[1])%2 == 0, items)), message='filter: half')
        else:
            table.update(items, message='filter: none')

    results = interactiveTable(
        tablelist,
        ['' ,"Episódios", "Nome"],
        "rcc",
        behaviour='multiSelectWithText',
        maxListSize=7,
        staticHighlights=staticHighlights,
        highlightRange=(2,2),
        filters=['none','half'],
        filter_callback=myfilter

    )
    print(results)

    print(results.text)

#  termios.tcsetattr(sys.stdin, termios.TCSADRAIN,filedescriptors)
    

