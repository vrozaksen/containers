#!/usr/bin/env bash

# Start the simple WP Pilot M3U service
echo "📺 Starting WP Pilot M3U Generator Service..."
echo "📊 Cache directory: /app/data"
echo "📺 M3U playlist URL: http://localhost:8080/playlist.m3u"
echo "📊 Status endpoint: http://localhost:8080/status"
echo "💡 Add ?epg=true/false to override EPG setting"

# Check required environment variables
if [ -z "$WPPILOT_USERNAME" ] || [ -z "$WPPILOT_PASSWORD" ] || [ -z "$WPPILOT_NETVICAPTCHA" ]; then
    echo "❌ Error: Required environment variables not set!"
    echo "   Please set:"
    echo "   - WPPILOT_USERNAME: Your WP Pilot username"
    echo "   - WPPILOT_PASSWORD: Your WP Pilot password"
    echo "   - WPPILOT_NETVICAPTCHA: netvicaptcha cookie value"
    exit 1
fi

echo "👤 Username: ${WPPILOT_USERNAME}"
echo "🔐 Password: [HIDDEN]"
echo "🍪 netvicaptcha: [HIDDEN]"

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

# Optional EPG by default
if [ "$ENABLE_EPG" = "true" ]; then
    echo "📅 EPG enabled by default"
fi


echo ""

exec python3 /app/wppilot_m3u.py $ARGS
