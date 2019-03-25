#!/usr/bin/env bash

read -p "This script requires the p7zip utility to unzip the dump: Do you want to install it? (y\n): " install_util

if [[ "$install_util" == "y" ]]; then
    case "$OSTYPE" in
    "darwin"*)
        echo "Mac system detected. Using homebrew."
        brew update && brew install p7zip
        ;;
    "linux-gnu")
        echo "Linux system detected. Using apt. Your admin password will be asked in order to install."
        sudo apt-get install p7zip-full
        ;;
    esac
fi

DIRECTORY=./stackexchange_dump/

if [[ ! -d "$DIRECTORY" ]]; then
    mkdir ./stackexchange_dump
fi

cd ./stackexchange_dump/

# Fetch and extract dataset
curl -L0 https://archive.org/download/stackexchange/apple.stackexchange.com.7z -o dump.7z       && \
7z x dump.7z && \
rm dump.7z


curl -L0 https://archive.org/download/stackexchange/readme.txt -o schema.txt



