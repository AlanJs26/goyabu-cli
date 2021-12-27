#!/usr/bin/env bash 

install_path="$HOME/.animedl"

sudo apt install python3 mpv python3-pip
pip3 install -r ./requirements.txt

mkdir -p $install_path
cp ./{animeScrapper,dropdown,anime,rawserver}.py $install_path
cp -r scrappers "$install_path/scrappers"
cp "$install_path/scrappers/*" "$install_path/scrappers/*"
echo "$(which python3) '$install_path/anime.py' \$@" > "$install_path/anime.sh"
sudo chmod u+x "$install_path/anime.sh"
sudo ln -sf "$install_path/anime.sh" "$HOME/.local/bin/anime"

printf "\ngoyabu-cli instalado com sucesso!\n\ndigite \033[92m'anime'\033[0m no terminal para começar\n"
