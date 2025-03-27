#!/bin/bash
set -e

echo "Starting Emby Server with data directory: ${EMBY_DATA:-/config}"

exec /opt/emby-server/bin/emby-server \
    --programdata "${EMBY_DATA:-/config}" \
    "$@"
