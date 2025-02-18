#!/usr/bin/env bash

#shellcheck disable=SC1091
test -f "/scripts/umask.sh" && source "/scripts/umask.sh"

#shellcheck disable=SC2086
exec \
    /usr/bin/python3 \
        /app/Kapowarr.py \
            --no-update \
            --config /config \
            "$@"