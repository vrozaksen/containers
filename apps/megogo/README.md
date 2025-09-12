# 📺 Megogo M3U Generator

Advanced M3U playlist generator for Megogo.net channels with device authentication support. Compatible with any IPTV player (Emby, Jellyfin, VLC, etc.).

## 🚀 Features

- **� Device Authentication**: Login with device code like smart TV apps
- **📺 Full Channel Access**: Access to premium channels after authentication
- **📻 TV & Radio**: Supports both television and radio channels
- **⏪ Catchup**: 7-day replay for supported channels
- **📊 EPG**: Current program information with titles and times
- **🚀 HTTP Server**: Built-in server for serving playlists
- **🐳 Docker**: Easy deployment with Docker
- **💾 Cache**: Channel list caching for better performance
- **🌐 Multi-language**: Configurable language support
- **🔗 Direct Streams**: Uses direct stream URLs (no Kodi dependency)

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
| `--login` | Login with device code | - |
| `--logout` | Logout and clear credentials | - |
| `--config` | Configuration file path | megogo_config.json |
| `--drm` | Enable DRM support | False |
| `--geo-zone` | Geographic zone | UA |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEGOGO_LANG` | Language for API calls (pl, uk, ru, etc.) | pl |
| `ENABLE_EPG` | Enable EPG by default (true/false) | false |
| `ENABLE_DRM` | Enable DRM support (true/false) | false |
| `GEO_ZONE` | Geographic zone (UA, PL, etc.) | UA |
| `REFRESH_INTERVAL` | Auto-refresh interval in seconds | 3600 |
| `CACHE_DURATION` | Cache duration in seconds | 3600 |
| `TZ` | Timezone | Europe/Warsaw |

### Standalone (Python)

```bash
# Install requirements
pip install requests

# Login with device code (required for premium channels)
python3 megogo_m3u.py --login --lang pl

# Generate M3U file (guest access - limited channels)
python3 megogo_m3u.py --output megogo.m3u

# Generate with EPG information (authenticated access - more channels)
python3 megogo_m3u.py --output megogo.m3u --epg

# Run as HTTP server
python3 megogo_m3u.py --server --port 8080

# Run with custom language
MEGOGO_LANG=uk python3 megogo_m3u.py --server --port 8080

# Logout when done
python3 megogo_m3u.py --logout
```

### Docker

```bash
# Build image
docker build -t megogo-m3u .

# Run container with persistent config
docker run -d \
  --name megogo-m3u \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e MEGOGO_LANG=pl \
  -e REFRESH_INTERVAL=7200 \
  megogo-m3u

# Login to get access to premium channels
docker exec -it megogo-m3u python3 /app/megogo_m3u.py --login --config /app/data/megogo_config.json --lang pl

# Run with EPG enabled by default
docker run -d \
  --name megogo-m3u-epg \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e MEGOGO_LANG=pl \
  -e ENABLE_EPG=true \
  megogo-m3u

# Run with Ukrainian language and DRM support
docker run -d \
  --name megogo-m3u-ua \
  -p 8081:8080 \
  -v $(pwd)/data-ua:/app/data \
  -e MEGOGO_LANG=uk \
  -e ENABLE_DRM=true \
  -e GEO_ZONE=UA \
  megogo-m3u

# Logout when needed
docker exec -it megogo-m3u python3 /app/megogo_m3u.py --logout --config /app/data/megogo_config.json
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
    volumes:
      - ./data:/app/data
    environment:
      - MEGOGO_LANG=pl
      - ENABLE_EPG=false
      - ENABLE_DRM=false
      - GEO_ZONE=UA
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

## � Authentication

### Device Authentication Process

1. **Start the login process**:
   ```bash
   python3 megogo_m3u.py --login --lang pl
   # or with Docker:
   docker exec -it megogo-m3u python3 /app/megogo_m3u.py --login --config /app/data/megogo_config.json --lang pl
   ```

2. **Get the device code**: The script will display a code like `X5WCY`

3. **Activate the device**:
   - Go to https://megogo.net/device
   - Enter the displayed code
   - Login with your Megogo account

4. **Automatic authentication**: The script will detect successful authentication and save credentials

### Channel Access

| Access Level | Channels | Description |
|--------------|----------|-------------|
| **Guest** | ~41 channels | Free channels, radio stations |
| **Authenticated** | ~62+ channels | Premium channels (Polsat, TVP 1, TVP 2, TV4, WP HD, etc.) |

### Authentication Management

```bash
# Check authentication status
curl http://localhost:8080/status

# Logout (clear credentials)
python3 megogo_m3u.py --logout
# or with Docker:
docker exec -it megogo-m3u python3 /app/megogo_m3u.py --logout --config /app/data/megogo_config.json
```

## �🔗 API Endpoints

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

### Authentication Issues

1. **Device already linked error**: The device was previously registered
   - Logout first: `python3 megogo_m3u.py --logout`
   - Or use a different config file: `--config different_config.json`

2. **Authentication timeout**: Code expired or network issues
   - Try again with a new login attempt
   - Check internet connection to megogo.net

3. **Token refresh errors**: Credentials may have expired
   - Re-authenticate: `python3 megogo_m3u.py --login`

### Common Issues

1. **Limited channels (41 instead of 62+)**: Not authenticated
   - Use `--login` to get premium channel access

2. **Stream playback errors**: Player-specific issues
   - Try different IPTV player (VLC, Emby, Jellyfin)
   - Some streams may require DRM support (`--drm` flag)

3. **No channels**: Network or API issues
   - Check connection to megogo.net
   - Verify language setting (`--lang pl/uk/ru`)

4. **EPG not showing**:
   - Use `?epg=true` parameter or `--epg` flag
   - EPG only available for some channels
3. **Slow loading**: Increase cache-duration

## 🏗️ Building

```bash
# Build from repository root (recommended)
cd /path/to/containers
docker build -f apps/megogo/Dockerfile -t megogo-m3u:latest .

# Multi-platform build (from repository root)
docker buildx bake -f apps/megogo/docker-bake.hcl image-all

# Local development and testing (requires just)
cd /path/to/containers
just local-build megogo
```

**Note**: Due to CI/CD requirements, the Dockerfile is designed to be built from the repository root directory, not from the app directory.

## 🧪 Testing

Tests use [goss](https://github.com/goss-org/goss) framework and verify:
- Python process is running
- Port 8080 is listening
- Status endpoint returns valid JSON
- M3U playlist endpoint works
- Generated playlist has correct format

Run tests with:
```bash
just local-build megogo
```

## 🎯 Compatibility

### IPTV Players
- ✅ **VLC Media Player** - Full support
- ✅ **Emby** - Full support with Live TV integration
- ✅ **Jellyfin** - Full support with Live TV integration
- ✅ **Plex** - Works with Live TV & DVR feature
- ✅ **IPTV Simple Client (Kodi)** - Direct stream support
- ✅ **Perfect Player** - Android/Smart TV
- ✅ **TiviMate** - Android TV
- ✅ **GSE Smart IPTV** - iOS/Android

### Stream Features
- ✅ **Live Streams** - Direct HLS/DASH URLs
- ✅ **Catchup/Timeshift** - 7-day replay for supported channels
- ✅ **EPG Integration** - Current program information
- ⚠️ **DRM Streams** - Limited support (use `--drm` flag)

### Supported Languages
- 🇵🇱 **Polish** (`pl`) - Default
- 🇺🇦 **Ukrainian** (`uk`)
- 🇷🇺 **Russian** (`ru`)
- 🇬🇧 **English** (`en`)

### Geographic Zones
- **UA** (Ukraine) - Default, most channels
- **PL** (Poland) - Polish content focus
- **RU** (Russia) - Russian content focus

## 📝 License

This project is for educational and personal use. Make sure you comply with Megogo's terms of service when using this software.

## ⚠️ Disclaimer

This is an unofficial tool for personal use. It is not affiliated with or endorsed by Megogo. Users are responsible for complying with Megogo's terms of service and applicable laws in their jurisdiction.
