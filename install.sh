#!/usr/bin/env bash 

sudo apt install python3 mpv python3-pip
pip3 install -r ./requirements.txt

mkdir -p "$HOME/Documentos/animedl"
cp ./{animeScrapper,dropdown,anime,rawserver}.py "$HOME/Documentos/animedl"
cp -r scrappers "$HOME/Documentos/animedl/scrappers"
cp "./scrappers/*" "$HOME/Documentos/animedl/scrappers/*"
echo "$(which python3) '$HOME/Documentos/animedl/anime.py' \$@" > "$HOME/Documentos/animedl/anime.sh"
sudo chmod u+x "$HOME/Documentos/animedl/anime.sh"
sudo ln -sf "$HOME/Documentos/animedl/anime.sh" "$HOME/.local/bin/anime"

printf "\ngoyabu-cli instalado com sucesso!\n\ndigite \033[92m'anime'\033[0m no terminal para começar\n"
