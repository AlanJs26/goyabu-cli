# goyabu-cli

<!--## assista animes diretamente do terminal-->
## 😎 Watch animes without leaving the terminal!

![Novo anime](https://github.com/AlanJs26/goyabu-cli/blob/main/img/record1.gif?raw=true)
![Retomando uma sessão anterior](https://github.com/AlanJs26/goyabu-cli/blob/main/img/record2.gif?raw=true)

<!--digite `anime` e siga as instruções para utilizar.-->
## 🚀 How to use



Type `anime` in the terminal to start the program

then you will be asked to type which anime/series you want to watch. After that, select one of the found anime/series, select the episodes you want to watch using the `spacebar` (or pressing enter to watch them all) and, finally, enjoy 😊.



<!--## ⚙ Instalação-->
## 📦 Installation

Requirements:
- Python 3
- MPV player (recommended)

Installation can be done using pip:

```bash
pip install goyabu-cli
```

<!--Com isso digitando `anime` no terminal, o programa deve funcionar-->

To run the program type `anime` in the terminal.

```bash
# run the bellow command to update the program
pip install --upgrade goyabu-cli
```


<!--## Instalação manual-->
## ⚙ Manual installation

Install Python 3, MPV and git 

Clone this repository 
```bash
git clone 'https://github.com/AlanJs26/goyabu-cli' && cd goyabu-cli
```

Install all pythons dependencies 
```bash
pip install -r requirements.txt
```

<!--Assim o programa pode ser executado com `python anime.py` -->
To run the program, type `python runner.py` in the program folder or add to your system path

## Available sources 

| Source                                                | Description                                                        | Language   | Comments           |
| ----------------------------------------------------- | ------------------------------------------------------------------ | ---------- | ------------------ |
| [animefire](https://animefire.com/) <!--animefire-->:heavy_check_mark:             | website used to watch anime                                        | Portuguese |                    |
| [goyabu](https://goyabu.com/)<!--goyabu-->:x:             | website used to watch anime                                        | Portuguese |                    |
| [superanimes](https://superanimes.biz/)<!--superanimes-->:x:             | website used to watch anime                                        | Portuguese |                    |
| [gogoanime](https://gogoanime.dk/)<!--gogoanime-->:x:             | website used to watch anime                                        | English |                    |
| [vizer](https://vizer.tv/)<!--vizer-->:x:             | website used to watch movies,tv shows and animes                                        | Portuguese,English |                    |

## Language

I'm Brazilian, so my primary focus is on portuguese sources for anime/series, but I have also translated the program to english and added some english sources.

## Compatibility

This app was tested on linux, but probably works in windows too. Some issues that windows users can have are:

- Lists not displaying properly
- MPV integration could not work
- file path issues

If you find some bug, please open and issue here on github.

## Tips

### Previous sessions

In the start screen you can press the `arrow up` or `Tab` to select something you have watched before. Or even type one of the numbers on the left instead of typing the whole name.

> All lists are scrollable, you check by looking for a little arrow at the top or bottom of the list.

As 1 will always be the last anime/series watched, you can use this in the command line to jump directly on your previous session.

```bash
anime 1 --yes
```

> Here I also used `--yes` to accept all prompts

### Command arguments

All available arguments are listed below:

> -  `--episodes` select which episodes to watch. The syntax is `start:end` or `episode`.
> -  `--player` specify the player do you want to use (default: mpv)
> -  `--scraper` use specified scraper to fetch the episodes
> -  `--update` fetch the number of total episodes of the items in history.
> -  `--server` serves a list of animes as a m3u playlist through the network.
> -  `--config` change the default config.
> -  `--anilist_sync` sync your local history with anilist
> -  `--yes` accept all default options. it is useful then you already know the full name of the anime/series
> -  `--config-dir` specify the folder to save the playlist file

for more information run `anime --help`

### Anilist

to enable anilist sync,to enable synchronization with anilist, you must first run the command `anime --config` and select the field 'token'. This will open a browser window asking for confirmation. 


### MPV

I strongly recommend the use of MPV player on top of this cli program, since with MPV is possible to start the stream at the exact point you left on the previous session.

I recommend my [MPV config](https://github.com/AlanJs26/mpv), it comes with a pretty ui, shaders and some plugins. One of them being `skiptosilence`, that is used to jump anime openings! (I have mapped `Tab` to activate it)



## To-do

- [x] upload project to pypi
- [ ] add more sources


