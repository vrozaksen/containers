#!/usr/bin/env bash

# Start the simple Megogo M3U service
echo "🎬 Starting Megogo M3U Generator Service..."
echo "📊 Cache directory: /app/data"
echo "📺 M3U playlist URL: http://localhost:8080/playlist.m3u"
echo "📊 Status endpoint: http://localhost:8080/status"
echo "💡 Add ?epg=true/false to override EPG setting"
echo "🌐 Language: ${MEGOGO_LANG:-pl}"
echo "📅 Default EPG: ${ENABLE_EPG:-false}"

# Prepare arguments from environment variables
ARGS="--server --host 0.0.0.0 --port 8080"

if [ -n "$REFRESH_INTERVAL" ]; then
    ARGS="$ARGS --refresh-interval $REFRESH_INTERVAL"
    echo "🔄 Auto-refresh interval: ${REFRESH_INTERVAL}s"
fi

if [ -n "$CACHE_DURATION" ]; then
    ARGS="$ARGS --cache-duration $CACHE_DURATION"
    echo "💾 Cache duration: ${CACHE_DURATION}s"
fi

echo ""

exec python3 /app/megogo_m3u.py $ARGS
