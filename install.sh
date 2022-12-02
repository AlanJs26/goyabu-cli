#!/usr/bin/env bash 

install_path="$HOME/.animedl"
tmp="$HOME/animedl_tmp"

exists()
{
  command -v "$1" >/dev/null 2>&1
}

if ! exists git && ! exists python3 && ! exists mpv; then
  sudo apt install python3 mpv python3-pip git
fi

if [ -d "./.git" ]; then
  tmp="."
else
  git clone https://github.com/AlanJs26/goyabu-cli $tmp
fi

python3 -m pip install -r $tmp/requirements.txt


mkdir -p $install_path
yes | cp $tmp/{animeScrapper,dropdown,anime,rawserver}.py $install_path -rf
yes | cp -rf "$tmp/scrappers" "$install_path"
# cp "$install_path/scrappers/*" "$install_path/scrappers/*"
echo "$(which python3) '$install_path/anime.py' \$@" > "$install_path/anime.sh"

if [ ! -x "$install_path/anime.sh" ]; then
  sudo chmod u+x "$install_path/anime.sh"
fi

if [ ! -f "$HOME/.local/bin/anime" ]; then
  sudo ln -sf "$install_path/anime.sh" "$HOME/.local/bin/anime"
fi

if [ ! -d "./.git" ]; then
  sudo rm -r $tmp
fi

printf "\ngoyabu-cli instalado com sucesso!\n\ndigite \033[92m'anime'\033[0m no terminal para começar\n"
