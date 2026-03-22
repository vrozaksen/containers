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

# --- Auto-update application.yml and youtube plugin ---
echo "Checking for Red-DiscordBot Lavalink updates..."

LATEST_RED_VERSION="$(curl -sf https://api.github.com/repos/Cog-Creators/Red-DiscordBot/releases/latest | jq -r '.tag_name' 2>/dev/null || echo "")"

if [ -n "$LATEST_RED_VERSION" ]; then
    YML_URL="https://github.com/Cog-Creators/Red-DiscordBot/releases/download/${LATEST_RED_VERSION}/Red-DiscordBot-${LATEST_RED_VERSION}-default-lavalink-application.yml"
    if curl -sf -o /tmp/application.yml "$YML_URL"; then
        # Preserve custom password if set
        if [ -f /data/application.yml ]; then
            CURRENT_PASS="$(grep -oP 'password:\s*\K\S+' /data/application.yml 2>/dev/null || echo "")"
        fi
        # Fix address for container use (Red defaults to localhost)
        sed -i 's/address: localhost/address: 0.0.0.0/' /tmp/application.yml
        mv /tmp/application.yml /data/application.yml
        # Restore custom password
        if [ -n "${CURRENT_PASS:-}" ] && [ "$CURRENT_PASS" != "youshallnotpass" ]; then
            sed -i "s/password: youshallnotpass/password: ${CURRENT_PASS}/" /data/application.yml
        fi
        echo "application.yml updated to Red ${LATEST_RED_VERSION}"
    else
        echo "Failed to download application.yml, using existing config"
    fi
else
    echo "Could not check for updates (no network?), using existing config"
fi

# First run fallback
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
