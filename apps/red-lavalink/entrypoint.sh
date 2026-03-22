#!/usr/bin/env bash
set -euo pipefail

# --- PUID/PGID setup ---
PUID="${PUID:-1000}"
PGID="${PGID:-100}"

if [ "$(id -u)" -eq 0 ]; then
    # Create/modify group — Alpine has no groupmod, so delete+recreate
    if getent group abc > /dev/null 2>&1; then
        CURRENT_GID="$(getent group abc | cut -d: -f3)"
        if [ "$CURRENT_GID" != "$PGID" ]; then
            delgroup abc 2>/dev/null || true
            addgroup -g "$PGID" -S abc
        fi
    else
        addgroup -g "$PGID" -S abc
    fi

    # Create/modify user — same pattern
    if getent passwd abc > /dev/null 2>&1; then
        CURRENT_UID="$(id -u abc)"
        if [ "$CURRENT_UID" != "$PUID" ]; then
            deluser abc 2>/dev/null || true
            adduser -u "$PUID" -G abc -s /bin/bash -D -H abc
        fi
    else
        adduser -u "$PUID" -G abc -s /bin/bash -D -H abc
    fi

    chown -R "$PUID:$PGID" /data
fi

# --- Default config ---
if [ ! -f /data/application.yml ]; then
    echo "No application.yml found, copying default..."
    cp /app/defaults/application.yml /data/application.yml
fi

# --- Launch Lavalink ---
if [ "$(id -u)" -eq 0 ]; then
    exec su-exec abc java \
        ${JAVA_OPTS:-} \
        -jar /app/Lavalink.jar \
        --spring.config.location=/data/application.yml \
        "$@"
else
    exec java \
        ${JAVA_OPTS:-} \
        -jar /app/Lavalink.jar \
        --spring.config.location=/data/application.yml \
        "$@"
fi
