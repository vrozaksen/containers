# 🎬 Megogo M3U Generator Service

A Docker container that generates M3U playlists from the Megogo TV service for use with media servers like Emby, Jellyfin, Plex, and other IPTV players.

## 🚀 Features

- **🔐 Secure Authentication**: Login with your Megogo credentials
- **📺 Live TV**: Generate M3U playlists with all available live channels
- **⏪ Catchup Support**: 7-day replay functionality for supported channels
- **📊 EPG Integration**: Optional current program information in channel names
- **🔄 Auto Token Refresh**: Automatic session management
- **🌐 Web Interface**: Easy-to-use web interface for configuration
- **🐳 Dockerized**: Easy deployment with Docker
- **📱 Multi-Platform**: Supports AMD64 and ARM64 architectures

## 📋 Prerequisites

- Docker installed on your system
- Valid Megogo account credentials
- Network access to Megogo services

## 🏗️ Building the Container

### Using Docker Bake (Recommended)

```bash
cd apps/megogo
docker buildx bake
```

### Using Docker Build

```bash
cd apps/megogo
docker build -t megogo-service .
```

## 🚀 Running the Container

### Quick Start

```bash
docker run -d \
  --name megogo-service \
  -p 8080:8080 \
  -v megogo-data:/app/data \
  ghcr.io/vrozaksen/megogo:latest
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  megogo:
    image: ghcr.io/vrozaksen/megogo:latest
    container_name: megogo-service
    ports:
      - "8080:8080"
    volumes:
      - megogo-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  megogo-data:
```

Then run:

```bash
docker-compose up -d
```

## ⚙️ Configuration

1. **Access the Web Interface**: Open `http://localhost:8080` in your browser
2. **Login**: Enter your Megogo email and password
3. **Configure Settings**: Adjust language and geographic zone if needed
4. **Get M3U URL**: Copy the generated M3U playlist URL

## 📺 Integration with Media Servers

### Emby / Jellyfin

1. Navigate to **Live TV** settings in your media server
2. Click **Add** next to **TV Tuners**
3. Select **M3U Tuner**
4. Enter the M3U URL: `http://your-server-ip:8080/playlist.m3u`
5. Optionally, set up EPG if your media server supports it
6. Save and refresh the TV guide

### Plex

1. Install the **IPTV** plugin for Plex
2. Configure it with the M3U URL: `http://your-server-ip:8080/playlist.m3u`

### VLC / Other Players

Simply open the M3U URL in your player: `http://your-server-ip:8080/playlist.m3u`

## 🔗 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Web interface |
| `GET /playlist.m3u` | M3U playlist |
| `GET /playlist.m3u?epg=true` | M3U playlist with EPG info |
| `GET /channels` | JSON list of channels |
| `GET /stream/{channel_id}` | Direct stream URL (redirects) |
| `GET /health` | Health check |
| `POST /login` | Login endpoint |
| `POST /logout` | Logout endpoint |
| `POST /config` | Update configuration |

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `Europe/Warsaw` | Timezone |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |

## 📁 Volume Mounts

- `/app/data` - Configuration and cache storage

## 🏥 Health Monitoring

The container includes a health check that verifies the service is responding:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{.State.Health}}' megogo-service
```

## 🔐 Security Notes

- The service requires your Megogo credentials to function
- Credentials are stored locally in the container's data volume
- All communication with Megogo uses HTTPS
- The web interface should be secured if exposed to the internet

## 🛠️ Troubleshooting

### Common Issues

1. **Login Failed**
   - Verify your Megogo credentials
   - Check if your account region matches the configured geo zone
   - Ensure network connectivity to Megogo services

2. **No Channels Available**
   - Confirm you're logged in successfully
   - Check if your Megogo subscription includes live TV
   - Verify geographic restrictions

3. **Streams Not Playing**
   - Check your media server's network access to the container
   - Verify the stream URLs are accessible from your media server
   - Check container logs for errors

### Viewing Logs

```bash
# View container logs
docker logs megogo-service

# Follow logs in real-time
docker logs -f megogo-service
```

### Container Shell Access

```bash
# Access container shell for debugging
docker exec -it megogo-service /bin/bash
```

## 🔄 Updates

To update to the latest version:

```bash
# Pull latest image
docker pull ghcr.io/vrozaksen/megogo:latest

# Recreate container
docker-compose down
docker-compose up -d
```

## 📝 Configuration Files

The service stores its configuration in `/app/data/config.json`. You can back up this file to preserve your settings.

## 🌐 Network Requirements

- Outbound HTTPS access to `api.megogo.net`
- Outbound HTTP/HTTPS access to Megogo CDN servers for streams
- Inbound access on port 8080 for the web interface and M3U access

## 📊 Performance

- Minimal resource usage (typically < 100MB RAM)
- Fast startup time (< 30 seconds)
- Efficient stream proxying with HTTP redirects
- Automatic token refresh to maintain sessions

## 🤝 Support

For issues and feature requests, please check the troubleshooting section above or create an issue in the repository.

## 📜 License

This project is provided as-is for educational and personal use. Ensure you comply with Megogo's terms of service when using this software.

## ⚠️ Disclaimer

This is an unofficial tool for personal use. It is not affiliated with or endorsed by Megogo. Users are responsible for complying with Megogo's terms of service and applicable laws in their jurisdiction.
