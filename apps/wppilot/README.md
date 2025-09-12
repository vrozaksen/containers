# WP Pilot M3U Generator

Docker container for generating M3U playlists from WP Pilot TV service. Based on the original Kodi plugin functionality.

## Features

- 📺 Generate M3U playlists from WP Pilot channels
- 📅 Optional EPG (Electronic Program Guide) support
- 🎬 Direct HLS stream URLs
- 🔄 Automatic cache refresh
- 🌐 HTTP API for remote access
- 🐳 Docker container ready

## Quick Start

### Requirements

You need valid WP Pilot credentials:
- Username and password
- `netvicaptcha` cookie value (obtained from browser when logged into WP Pilot)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WPPILOT_USERNAME` | Yes | Your WP Pilot username |
| `WPPILOT_PASSWORD` | Yes | Your WP Pilot password |
| `WPPILOT_NETVICAPTCHA` | Yes | netvicaptcha cookie value from browser |
| `REFRESH_INTERVAL` | No | Cache refresh interval in seconds (default: 3600) |
| `CACHE_DURATION` | No | Cache duration in seconds (default: 3600) |
| `ENABLE_EPG` | No | Enable EPG by default (default: false) |


### Docker Run

```bash
docker run -d \
  --name wppilot-m3u \
  -p 8080:8080 \
  -e WPPILOT_USERNAME="your_username" \
  -e WPPILOT_PASSWORD="your_password" \
  -e WPPILOT_NETVICAPTCHA="your_cookie_value" \
  wppilot-m3u:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  wppilot:
    image: wppilot-m3u:latest
    container_name: wppilot-m3u
    ports:
      - "8080:8080"
    environment:
      - WPPILOT_USERNAME=your_username
      - WPPILOT_PASSWORD=your_password
      - WPPILOT_NETVICAPTCHA=your_netvicaptcha_cookie
      - REFRESH_INTERVAL=3600
      - ENABLE_EPG=false
    restart: unless-stopped
```

## Usage

### HTTP Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/playlist.m3u` | Get M3U playlist | `?epg=true/false` |
| `/status` | Service status | None |

### Examples

```bash
# Basic playlist
curl http://localhost:8080/playlist.m3u

# Playlist with EPG
curl http://localhost:8080/playlist.m3u?epg=true

# Service status
curl http://localhost:8080/status
```

### Command Line Usage

```bash
# Generate playlist file
python3 wppilot_m3u.py --output playlist.m3u --username USER --password PASS --netvicaptcha COOKIE

# Include EPG
python3 wppilot_m3u.py --output playlist.m3u --epg --username USER --password PASS --netvicaptcha COOKIE

# Run as server
python3 wppilot_m3u.py --server --port 8080 --username USER --password PASS --netvicaptcha COOKIE
```

## Getting netvicaptcha Cookie

The `netvicaptcha` cookie is automatically set during the WP Pilot login process and is required for API authentication.

### Method 1: Extract from Browser (Recommended)
1. Open WP Pilot in your browser
2. Login to your account
3. Open browser developer tools (F12)
4. Go to Application/Storage tab → Cookies → https://pilot.wp.pl
5. Find the `netvicaptcha` cookie and copy its value
6. Use this value as `WPPILOT_NETVICAPTCHA`

### Method 2: Network Tab
1. Open WP Pilot in your browser
2. Login to your account
3. Open browser developer tools (F12)
4. Go to Network tab
5. Make any request to pilot.wp.pl
6. Look for the `netvicaptcha` cookie value in the request headers
7. Copy this value to use as `WPPILOT_NETVICAPTCHA`

**Note**: The `netvicaptcha` cookie may expire and need to be refreshed periodically.

## Building

```bash
# Build from repository root (recommended)
cd /path/to/containers
docker build -f apps/wppilot/Dockerfile -t wppilot-m3u:latest .

# Multi-platform build (from repository root)
docker buildx bake -f apps/wppilot/docker-bake.hcl image-all

# Local development and testing (requires just)
cd /path/to/containers
just local-build wppilot
```

**Note**: Due to CI/CD requirements, the Dockerfile is designed to be built from the repository root directory, not from the app directory.

## Testing

Tests use [goss](https://github.com/goss-org/goss) framework and verify:
- Python process is running
- Port 8080 is listening
- Status endpoint returns valid JSON
- Service responds correctly

Run tests with:
```bash
just local-build wppilot
```

## Stream URLs

- Format: `https://.../*.m3u8` (HLS streams)
- Works with any M3U8-compatible player (VLC, IPTV apps, etc.)
- Requires authentication for each channel
- May have rate limiting

## Troubleshooting

### Login Issues
- Verify username and password
- Ensure `netvicaptcha` cookie is current (may expire)
- Check if account has active subscription

### No Channels
- Verify login credentials
- Check subscription status
- Look at logs for authentication errors

### Stream Playback Issues
- Check network connectivity and player compatibility
- Ensure your player supports HLS/M3U8 streams
- Some streams may have geographical restrictions

## API Response Examples

### Status Response
```json
{
  "status": "ok",
  "logged_in": true,
  "channels_count": 45,
  "packets": ["WP Pilot Sport", "WP Pilot Premium"],
  "last_update": "2024-01-20T10:30:00"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Authentication failed"
}
```

## License

Based on the original WP Pilot Kodi plugin. For educational and personal use only.

## Disclaimer

This tool is for personal use with your own WP Pilot subscription. Respect the terms of service of WP Pilot.
