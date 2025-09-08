# 📺 Emby Integration Guide for Megogo Service

This guide will walk you through setting up the Megogo M3U service with Emby Media Server.

## 🔧 Step 1: Deploy the Megogo Service

### Option A: Using Docker Compose (Recommended)

1. Save the following as `docker-compose.yml`:

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
    environment:
      - TZ=Europe/Warsaw
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  megogo-data:
```

2. Start the service:
```bash
docker-compose up -d
```

### Option B: Using Docker Run

```bash
docker run -d \
  --name megogo-service \
  -p 8080:8080 \
  -v megogo-data:/app/data \
  --restart unless-stopped \
  ghcr.io/vrozaksen/megogo:latest
```

## 🔐 Step 2: Configure Authentication

1. Open your browser and go to `http://localhost:8080` (or `http://your-server-ip:8080`)
2. Enter your Megogo credentials:
   - **Email**: Your Megogo account email
   - **Password**: Your Megogo account password
3. Click "Login" and wait for confirmation
4. Verify you see "✅ Logged in successfully" status

## 📺 Step 3: Configure Emby Live TV

### Add M3U Tuner

1. Open Emby Admin Dashboard
2. Navigate to **Live TV** → **TV Tuners**
3. Click **Add** or **+** button
4. Select **M3U Tuner** from the tuner type list

### Configure M3U Tuner Settings

Fill in the following information:

- **M3U Url**: `http://your-server-ip:8080/playlist.m3u`
  - Replace `your-server-ip` with the actual IP address of your Docker host
  - If Emby is running on the same machine, you can use `http://localhost:8080/playlist.m3u`

- **User Agent**: `Emby Live TV` (optional)

- **Tuner Count**: `1` (you can increase this if needed)

- **Enable automatic updates**: ✅ Checked

### Advanced Settings (Optional)

- **Buffer path**: Leave default or specify a path for buffering
- **Enable channel logos**: ✅ Checked (logos are included in the M3U)
- **Enable catchup/replay**: ✅ Checked (for supported channels)

## 📊 Step 4: Configure Channel Guide

### Option A: Use Megogo EPG (Basic)

The M3U playlist includes basic current program information. To get this:

1. Use the EPG-enabled playlist URL: `http://your-server-ip:8080/playlist.m3u?epg=true`
2. In Emby, the current program will be shown in channel names

### Option B: External EPG Provider (Advanced)

For a full TV guide, you can integrate an external EPG provider:

1. In Emby Live TV settings, go to **Guide Data Providers**
2. Add a compatible EPG source (XMLTV format)
3. Map the channel IDs to match your M3U playlist

## 🔧 Step 5: Finalize Setup

### Refresh Guide Data

1. In Emby Admin → **Live TV**
2. Click **Refresh Guide Data**
3. Wait for the process to complete

### Test Channels

1. Go to **Live TV** in Emby
2. Check that channels are visible
3. Try playing a live channel
4. Test catchup functionality (if available for the channel)

## 🛠️ Troubleshooting

### Channels Not Appearing

1. **Check Service Status**:
   ```bash
   docker logs megogo-service
   ```

2. **Verify M3U URL**:
   - Open `http://your-server-ip:8080/playlist.m3u` in a browser
   - You should see an M3U playlist with channel entries

3. **Check Network Connectivity**:
   - Ensure Emby can reach the Megogo service
   - Test from Emby server: `curl http://your-server-ip:8080/health`

### Streams Not Playing

1. **Network Access**: Ensure Emby server can access both:
   - The Megogo service (port 8080)
   - External Megogo CDN servers (for actual streams)

2. **Check Stream URLs**:
   - Visit `http://your-server-ip:8080/channels` to see available channels
   - Test a direct stream: `http://your-server-ip:8080/stream/CHANNEL_ID`

3. **Authentication Issues**:
   - Verify login status at `http://your-server-ip:8080`
   - Re-login if necessary

### Performance Issues

1. **Increase Buffer Size** in Emby Live TV settings
2. **Adjust Tuner Count** based on concurrent viewing needs
3. **Monitor Resources**:
   ```bash
   docker stats megogo-service
   ```

## 🔄 Maintenance

### Updating the Service

```bash
# Pull latest image
docker pull ghcr.io/vrozaksen/megogo:latest

# Recreate container
docker-compose down
docker-compose up -d
```

### Backing Up Configuration

```bash
# Backup configuration
docker cp megogo-service:/app/data/config.json megogo-config-backup.json
```

### Monitoring Health

```bash
# Check container health
docker ps

# View service logs
docker logs -f megogo-service

# Test health endpoint
curl http://localhost:8080/health
```

## 📱 Additional Features

### Catchup/Replay

For channels that support it, you can watch programs from the past 7 days:

1. In Emby, look for the "Catchup" or "Replay" option
2. Select the time period you want to watch
3. The service will automatically find the corresponding program

### Mobile Access

The M3U playlist also works with mobile apps:

- **Emby Mobile Apps**: Full integration with all features
- **IPTV Players**: Use the M3U URL directly in apps like IPTV Smarters, TiviMate, etc.

## 🔐 Security Considerations

### Network Security

- The service runs on port 8080 by default
- Consider using a reverse proxy with HTTPS for external access
- Restrict access to your local network if possible

### Credentials

- Your Megogo credentials are stored locally in the Docker volume
- The service automatically refreshes authentication tokens
- No credentials are logged or transmitted to third parties

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the main README.md for additional information
3. Check container logs for error messages
4. Ensure your Megogo account is active and has live TV access

## 📋 Quick Reference

| Component | URL/Command |
|-----------|-------------|
| Web Interface | `http://your-server-ip:8080` |
| M3U Playlist | `http://your-server-ip:8080/playlist.m3u` |
| M3U with EPG | `http://your-server-ip:8080/playlist.m3u?epg=true` |
| Health Check | `http://your-server-ip:8080/health` |
| View Logs | `docker logs megogo-service` |
| Restart Service | `docker-compose restart megogo` |

## ✅ Success Checklist

- [ ] Megogo service is running and accessible
- [ ] Successfully logged in with Megogo credentials
- [ ] M3U URL returns a valid playlist
- [ ] Emby Live TV tuner is configured
- [ ] Channels appear in Emby Live TV
- [ ] Streams play correctly
- [ ] Catchup functionality works (if supported)

---

🎉 **Congratulations!** You now have Megogo integrated with Emby for live TV streaming and catchup functionality.
