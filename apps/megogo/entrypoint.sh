#!/usr/bin/env bash

# Start the Enhanced Megogo service
echo "🎬 Starting Enhanced Megogo M3U Generator Service..."
echo "📊 Data directory: /app/data"
echo "🌐 Web interface will be available at: http://localhost:8080"
echo "📺 M3U playlist URL: http://localhost:8080/playlist.m3u"
echo ""

exec python3 /app/enhanced_megogo_service.py
