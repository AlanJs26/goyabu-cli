#!/usr/bin/env bash 

sudo apt install python3 mpv python3-pip
pip3 install -r ./requirements.txt

mkdir "$HOME/Documentos/animedl"
cp anime.py "$HOME/Documentos/animedl"
echo "$(which python3) '$HOME/Documentos/animedl/anime.py' \$@" > "$HOME/Documentos/animedl/anime.sh"
chmod u+x "$HOME/Documentos/animedl/anime.sh"
ln "$HOME/Documentos/animedl/anime.sh" "$HOME/.local/bin/anime"
#ln "$HOME/Documentos/animedl/anime.sh" anime
