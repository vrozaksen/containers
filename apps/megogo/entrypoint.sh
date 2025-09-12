#!/usr/bin/env bash

# Configuration file path
CONFIG_FILE="/app/data/megogo_config.json"

# Start the Megogo M3U Generator Service
echo "🎬 Starting Megogo M3U Generator Service..."
echo "📊 Data directory: /app/data"
echo "� Config file: $CONFIG_FILE"
echo "�📺 M3U playlist URL: http://localhost:8080/playlist.m3u"
echo "📊 Status endpoint: http://localhost:8080/status"
echo "💡 Add ?epg=true/false to override EPG setting"
echo "🌐 Language: ${MEGOGO_LANG:-pl}"
echo "📅 Default EPG: ${ENABLE_EPG:-false}"
echo "🔒 DRM Support: ${ENABLE_DRM:-false}"
echo "🌍 Geographic zone: ${GEO_ZONE:-UA}"

# Prepare arguments from environment variables
ARGS="--server --host 0.0.0.0 --port 8080 --config $CONFIG_FILE"

if [ -n "$REFRESH_INTERVAL" ]; then
    ARGS="$ARGS --refresh-interval $REFRESH_INTERVAL"
    echo "🔄 Auto-refresh interval: ${REFRESH_INTERVAL}s"
fi

if [ -n "$CACHE_DURATION" ]; then
    ARGS="$ARGS --cache-duration $CACHE_DURATION"
    echo "💾 Cache duration: ${CACHE_DURATION}s"
fi

if [ "${ENABLE_DRM:-false}" = "true" ]; then
    ARGS="$ARGS --drm"
fi

if [ -n "$GEO_ZONE" ]; then
    ARGS="$ARGS --geo-zone $GEO_ZONE"
fi

echo ""
echo "🚀 Starting server with authentication support..."
echo "📱 To authenticate: docker exec -it <container> python3 /app/megogo_m3u.py --login --config $CONFIG_FILE"
echo "👋 To logout: docker exec -it <container> python3 /app/megogo_m3u.py --logout --config $CONFIG_FILE"
echo ""

exec python3 /app/megogo_m3u.py $ARGS
