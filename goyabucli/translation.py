from locale import getdefaultlocale
from rich import print as rprint

translation = {
    "Nenhum anime encontrado com o nome '{}'": {
        'en': "Wasn't found any anime named '{}'",
    },
    "Animes": {
        'en': 'Animes',
    },
    "Fonte": {
        'en': 'Source',
    },
    "Anime Selecionado": {
        'en': 'Selected Anime',
    },
    "Escolha uma fonte": {
        'en': 'Choose and source',
    },
    "Não foi possível selecionar uma fonte": {
        'en': "Wasn't possible to select and source",
    },
    "Não foi possível acessar os episódios de '{}' usando '{}'": {
        'en': "Wasn't possible fetch the episodes of '{}' using '{}' as source",
    },
    "Episodios": {
        'en': 'Episodes',
    },
    "deseja assistir todos os episódios? [S/n]: ": {
        'en': 'do you want watch all episodes? [Y/n]: ',
    },
    "É possível selecionar os episódios usando 'c' ou a barra de espaço": {
        'en': "You can select episodes using 'c' or the 'space bar'",
    },
    "Links carregados": {
        'en': 'Loaded links',
    },
    'Abrindo "{}"...': {
        'en': "Loading '{}'...",
    },
    "Digite: ": {
        'en': 'Type: ',
    },
    "Episodio {} [{}/{}]": {
        'en': 'Episode {} [{}/{}]',
    },
    "Completo": {
        'en': 'Complete',
    },
    "Sessoes anteriores": {
        'en': 'Last sessions',
    },
    "Status": {
        'en': 'Status',
    },
    "Atualizando o histórico...": {
        'en': 'Updating history...',
    },
    "Animes atualizados": {
        'en': 'animes updated',
    },
    "Não foi encontrado nenhum link válido para o episódio {} atualizados": {
        'en': "Wasn't found any valid links for episode {}",
    },
    "Não foi possível gerar o arquivo m3u": {
        'en': "Wasn't possible generate the m3u file",
    },
}

lang = 'en'
sysLang = getdefaultlocale()[0]
if sysLang and sysLang[0:2] == 'pt':
    lang = 'pt'

def t(text:str, *args):
    if lang == 'pt':
        translation_text = text
    else:
        translation_text = translation[text][lang]

    if args:
        return translation_text.format(*args)

    return translation_text


def error(string):
    rprint('[red]'+string)

