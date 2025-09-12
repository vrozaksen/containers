# 📺 Megogo M3U Generator

Simple M3U playlist generator from free Megogo.net channels. Based on Kodi plugin functionality for Megogo.

## 🚀 Features

- **📺 Free Channels**: Generate M3U playlists from free Megogo channels
- **📻 TV & Radio**: Supports both television and radio channels
- **⏪ Catchup**: 7-day replay for supported channels
- **📊 EPG**: Optional current program information
- **🚀 HTTP Server**: Built-in server for serving playlists
- **🐳 Docker**: Easy deployment with Docker
- **💾 Cache**: Channel list caching for better performance
- **🌐 Multi-language**: Configurable language support

## 📋 Requirements

- Python 3.7+ (for standalone version)
- Docker (for containerized version)
- Internet connection with access to Megogo.net

## 🚀 Usage

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--output`, `-o` | Output M3U file path | Auto-generated |
| `--epg` | Include current program information | False |
| `--server` | Run as HTTP server | False |
| `--port` | HTTP server port | 8080 |
| `--host` | Server IP address | 0.0.0.0 |
| `--refresh-interval` | Cache refresh interval (seconds) | 3600 |
| `--cache-duration` | Cache lifetime (seconds) | 3600 |
| `--lang` | API language | From env or 'pl' |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEGOGO_LANG` | Language for API calls (pl, uk, ru, etc.) | pl |
| `ENABLE_EPG` | Enable EPG by default (true/false) | false |
| `REFRESH_INTERVAL` | Auto-refresh interval in seconds | 3600 |
| `CACHE_DURATION` | Cache duration in seconds | 3600 |
| `TZ` | Timezone | Europe/Warsaw |

### Standalone (Python)

```bash
# Install requirements
pip install requests

# Generate M3U file
python3 megogo_m3u.py --output megogo.m3u

# Generate with EPG information
python3 megogo_m3u.py --output megogo.m3u --epg

# Run as HTTP server
python3 megogo_m3u.py --server --port 8080

# Run with custom language
MEGOGO_LANG=uk python3 megogo_m3u.py --server --port 8080
```

### Docker

```bash
# Build image
docker build -t megogo-m3u .

# Run container
docker run -d \
  --name megogo-m3u \
  -p 8080:8080 \
  -e MEGOGO_LANG=pl \
  -e REFRESH_INTERVAL=7200 \
  megogo-m3u

# Run with EPG enabled by default
docker run -d \
  --name megogo-m3u-epg \
  -p 8080:8080 \
  -e MEGOGO_LANG=pl \
  -e ENABLE_EPG=true \
  megogo-m3u

# Run with Ukrainian language
docker run -d \
  --name megogo-m3u-ua \
  -p 8081:8080 \
  -e MEGOGO_LANG=uk \
  megogo-m3u
```

### Docker Compose

```yaml
version: '3.8'

services:
  megogo-m3u:
    build: .
    container_name: megogo-m3u
    ports:
      - "8080:8080"
    environment:
      - MEGOGO_LANG=pl
      - ENABLE_EPG=false
      - REFRESH_INTERVAL=3600
      - CACHE_DURATION=3600
      - TZ=Europe/Warsaw
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/status"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker Bake

```bash
docker buildx bake
```

## 🔗 API Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /` | M3U playlist | `?epg=true/false` to override default EPG |
| `GET /playlist.m3u` | M3U playlist | `?epg=true/false` to override default EPG |
| `GET /status` | Server status | - |

## 📺 Integration Examples

### Jellyfin/Emby

1. Go to **Live TV** settings
2. Add **M3U Tuner**
3. Enter URL: `http://your-server:8080/playlist.m3u`
4. Enable EPG: `http://your-server:8080/playlist.m3u?epg=true`

### VLC Player

```bash
vlc http://your-server:8080/playlist.m3u
```

### IPTV Simple Client (Kodi)

- M3U URL: `http://your-server:8080/playlist.m3u`
- EPG URL: Not supported yet

## 🔧 Troubleshooting

### Check logs

```bash
# Container logs
docker logs megogo-m3u

# Live logs
docker logs -f megogo-m3u
```

### Common issues

1. **No channels**: Check connection to megogo.net
2. **Stream errors**: URLs may require additional DRM handling
3. **Slow loading**: Increase cache-duration

## 🏗️ Building

```bash
# Build locally
docker build -t megogo-m3u .

# Use docker bake
docker buildx bake
```

## 📝 License

This project is for educational and personal use. Make sure you comply with Megogo's terms of service when using this software.

## ⚠️ Disclaimer

This is an unofficial tool for personal use. It is not affiliated with or endorsed by Megogo. Users are responsible for complying with Megogo's terms of service and applicable laws in their jurisdiction.
