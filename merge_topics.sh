#!/usr/bin/env bash

if [[ "$#" -lt 2 ]]; then
    echo "You should specify at least 2 domains to merge"
    exit -1
fi

BASE_DIRECTORY=./stackexchange_dump/

if [[ ! -d "$BASE_DIRECTORY" ]]; then
    echo "Base Directory (stackexchange_dump) does not exist"
    exit -1
fi

is_valid=1
file_name="merge"

for domain in "$@"
do
    if [[ ! -f "$BASE_DIRECTORY/$domain/Posts.xml" ]]; then
        echo "Necessary Files for domain $domain do not exist"
        is_valid=0
    fi
    file_name+="_$domain"
done

if [[ "$is_valid" -eq 0 ]]; then
    exit -1
fi

if [[ -f "$file_name" ]]; then
    rm "$file_name"
    rm "$file_name""_lookup"
fi

cd "$BASE_DIRECTORY"

current_line=0
for domain in "$@"
do
    cat "$domain/data_train.tsv" >> "$file_name"".tsv"
    echo "$current_line" >> "$file_name""_lookup"
    current_line=$((current_line + $(($(wc -l < "$domain/data_train.tsv"))) ))
done