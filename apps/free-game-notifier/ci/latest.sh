#!/usr/bin/env bash
version="$(curl -sX GET "https://api.github.com/repos/j6nca/free-game-notifier/releases/latest" | jq --raw-output '.tag_name')"
version="${version#*v}"
version="${version#*release-}"
printf "%s" "${version}"
