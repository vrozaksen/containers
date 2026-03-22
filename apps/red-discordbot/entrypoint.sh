#!/usr/bin/env bash
set -euo pipefail

# --- PUID/PGID setup ---
PUID="${PUID:-1000}"
PGID="${PGID:-100}"

if [ "$(id -u)" -eq 0 ]; then
    # Create/modify group
    if getent group abc > /dev/null 2>&1; then
        groupmod -o -g "$PGID" abc
    else
        addgroup --gid "$PGID" abc
    fi

    # Create/modify user
    if getent passwd abc > /dev/null 2>&1; then
        usermod -o -u "$PUID" -g "$PGID" abc
    else
        adduser --uid "$PUID" --gid "$PGID" --no-create-home --disabled-password --gecos "" abc
    fi

    chown -R "$PUID:$PGID" /data
fi

# --- Venv management ---
VENV_PATH="/data/venv"
CURRENT_PY="$(python --version 2>&1)"

if [ -d "$VENV_PATH" ]; then
    VENV_PY="$("$VENV_PATH/bin/python" --version 2>&1 || echo "none")"
    if [ "$CURRENT_PY" != "$VENV_PY" ]; then
        echo "Python version changed ($VENV_PY → $CURRENT_PY), recreating venv..."
        rm -rf "$VENV_PATH"
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python -m venv "$VENV_PATH"
fi

# shellcheck disable=SC1091
. "$VENV_PATH/bin/activate"

# --- Update Red-DiscordBot ---
INSTALLED_VERSION=""
if [ -f /data/.redbotversion ]; then
    INSTALLED_VERSION="$(cat /data/.redbotversion)"
fi

if [ -n "${REDBOT_VERSION:-}" ]; then
    TARGET_PACKAGE="Red-DiscordBot[postgres]==${REDBOT_VERSION}"
else
    TARGET_PACKAGE="Red-DiscordBot[postgres]"
fi

if [ "$INSTALLED_VERSION" != "${REDBOT_VERSION:-latest}" ]; then
    echo "Updating Red-DiscordBot..."
    pip install --no-cache-dir --upgrade "$TARGET_PACKAGE" 2>&1
    if [ -n "${REDBOT_VERSION:-}" ]; then
        echo "$REDBOT_VERSION" > /data/.redbotversion
    else
        echo "latest" > /data/.redbotversion
    fi
fi

# --- Ensure instance registry exists ---
# Red-DiscordBot stores instance registry at $HOME/.config/Red-DiscordBot/config.json
# This is separate from /data/config.json (instance data config)
# We must ensure the registry always points to /data for instance "docker"
REGISTRY_DIR="${HOME}/.config/Red-DiscordBot"
REGISTRY_FILE="${REGISTRY_DIR}/config.json"
mkdir -p "$REGISTRY_DIR"

if [ -f /data/config.json ]; then
    # Existing data — read storage type from existing config
    EXISTING_STORAGE="$(jq -r '.docker.STORAGE_TYPE // "JSON"' /data/config.json)"
    echo '{"docker": {"DATA_PATH": "/data", "COG_PATH_APPEND": "cogs", "CORE_PATH_APPEND": "core", "STORAGE_TYPE": "'"$EXISTING_STORAGE"'", "STORAGE_DETAILS": {}}}' | jq . > "$REGISTRY_FILE"
    echo "Instance registry restored (storage: $EXISTING_STORAGE)"
else
    # First run — create instance via redbot-setup
    echo "First run detected — setting up Red-DiscordBot instance..."
    STORAGE="${STORAGE_TYPE:-json}"

    if [ "$STORAGE" = "postgres" ]; then
        redbot-setup --no-prompt \
            --instance-name docker \
            --data-path /data \
            --storage-type postgres \
            --no-cogs
    else
        redbot-setup --no-prompt \
            --instance-name docker \
            --data-path /data \
            --storage-type json \
            --no-cogs
    fi
fi

# --- Inject one-time env vars ---
if [ -n "${TOKEN:-}" ] && [ -f /data/config.json ]; then
    CURRENT_TOKEN="$(jq -r '.docker.TOKEN // empty' /data/core/settings.json 2>/dev/null || echo "")"
    if [ -z "$CURRENT_TOKEN" ]; then
        echo "Setting bot token..."
        redbot docker --edit --no-prompt --token "$TOKEN" 2>/dev/null || true
    fi
fi

if [ -n "${OWNER:-}" ] && [ -f /data/config.json ]; then
    echo "Setting owner..."
    redbot docker --edit --no-prompt --owner "$OWNER" 2>/dev/null || true
fi

# Set prefixes if provided
PREFIXES=""
for i in "" 2 3 4 5; do
    VAR="PREFIX${i}"
    VAL="${!VAR:-}"
    if [ -n "$VAL" ]; then
        PREFIXES="${PREFIXES} --prefix ${VAL}"
    fi
done
if [ -n "$PREFIXES" ]; then
    # shellcheck disable=SC2086
    redbot docker --edit --no-prompt $PREFIXES 2>/dev/null || true
fi

# --- Main loop ---
while true; do
    EXIT_CODE=0
    if [ "$(id -u)" -eq 0 ]; then
        # shellcheck disable=SC2086
        gosu abc redbot docker --no-prompt ${EXTRA_ARGS:-} "$@" || EXIT_CODE=$?
    else
        # shellcheck disable=SC2086
        redbot docker --no-prompt ${EXTRA_ARGS:-} "$@" || EXIT_CODE=$?
    fi

    # Exit code 26 = restart requested via [p]restart
    if [ "$EXIT_CODE" -eq 26 ]; then
        echo "Restart requested, restarting..."
        continue
    fi

    exit "$EXIT_CODE"
done
