#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Megogo M3U Generator
Simple script to generate M3U playlists from free Megogo.net channels
Based on the Kodi plugin functionality for Megogo
"""

import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)

# Constants from original Kodi plugin
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0'
BASE_URL = 'https://megogo.net/'

HEADERS = {
    'referer': BASE_URL,
    'User-Agent': UA
}

class MegogoM3UGenerator:
    def __init__(self, cache_duration=3600, lang='pl', default_epg=False):
        self.session = requests.Session()
        self.channels_cache = None
        self.cache_time = 0
        self.cache_duration = cache_duration  # Default 1 hour
        self.auto_refresh = False
        self.refresh_thread = None
        self.lang = lang  # Language for API calls
        self.default_epg = default_epg  # Default EPG setting

    def get_channels(self):
        """Fetches channel list from Megogo (copy from Kodi plugin)"""
        # Channel cache
        if self.channels_cache and (time.time() - self.cache_time) < self.cache_duration:
            return self.channels_cache

        try:
            url = BASE_URL + f'wb/epgModule_v1/tvChannelsGrouped?lang={self.lang}'
            resp = self.session.get(url, headers=HEADERS, timeout=10).json()

            c_groups = resp['data']['widgets']['epgModule_v1']['json']['channel_groups']
            chans = []
            for g in c_groups:
                chans += g['objects']

            ids = []
            channels = []
            for c in chans:
                if c['vod_channel'] == False and c['is_available'] and c['id'] not in ids:
                    channels.append(c)
                    ids.append(c['id'])

            self.channels_cache = channels
            self.cache_time = time.time()
            return channels

        except Exception as e:
            print(f"❌ Error fetching channels: {e}")
            return []

    def get_epg_live(self, channel_ids):
        """Fetches current program for channels (optional)"""
        try:
            since = int(time.time())
            till = since + 8 * 60 * 60
            url = BASE_URL + f'wb/epgModule_v1/epg?channel_id={channel_ids}&locale={self.lang}&from={since}&to={till}&lang={self.lang}'
            resp = self.session.get(url, headers=HEADERS, timeout=10).json()

            chans = resp['data']['widgets']['epgModule_v1']['json']
            epg = {}
            for c in chans:
                cid = str(c['id'])
                e = ''
                for p in c['programs']:
                    title = p['title']
                    since_time = datetime.fromtimestamp(p['start_timestamp']).strftime('%H:%M')
                    e += f'{since_time} {title}\n'
                epg[cid] = e.strip()
            return epg
        except Exception as e:
            print(f"⚠️  Error fetching EPG: {e}")
            return {}

    def generate_m3u(self, include_epg=False, output_file=None):
        """Generates M3U playlist"""
        print("📺 Fetching channel list from Megogo...")
        channels = self.get_channels()

        if not channels:
            print("❌ Failed to fetch channels")
            return None

        print(f"✅ Found {len(channels)} channels")

        # Optionally fetch EPG
        epg = {}
        if include_epg:
            print("📅 Fetching program information...")
            channel_ids = ','.join([str(c['id']) for c in channels])
            epg = self.get_epg_live(channel_ids)

        # Generate M3U
        m3u_content = '#EXTM3U\n'

        for c in channels:
            if c['vod_channel'] == False and c['is_available']:
                channel_id = str(c['id'])
                channel_name = c['title']
                channel_logo = c['image']['original']

                # Check if it's radio or TV
                is_radio = 40625 in c['genres'] if 'genres' in c else False
                group_title = "Megogo Radio" if is_radio else "Megogo TV"

                # Add EPG information to channel name if available
                display_name = channel_name
                if include_epg and channel_id in epg and epg[channel_id]:
                    current_program = epg[channel_id].split('\n')[0] if epg[channel_id] else ''
                    if current_program:
                        display_name = f"{channel_name} • {current_program}"

                # Stream URL (direct link to Megogo)
                stream_url = f"https://megogo.net/wb/videoEmbed_v2/stream?lang={self.lang}&obj_id={channel_id}&drm_type=modular"

                # Catchup for channels with DVR function
                if c.get('is_dvr', False):
                    m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-logo="{channel_logo}" group-title="{group_title}" catchup="append" catchup-source="&s={{utc:Y-m-dTH:M:S}}&e={{utcend:Y-m-dTH:M:S}}" catchup-days="7",{display_name}\n'
                else:
                    m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-logo="{channel_logo}" group-title="{group_title}",{display_name}\n'

                m3u_content += f"{stream_url}\n"

        # Save to file or return content
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(m3u_content)
                print(f"✅ Playlist saved to: {output_file}")
                return output_file
            except Exception as e:
                print(f"❌ File write error: {e}")
                return None
        else:
            return m3u_content

    def start_auto_refresh(self, interval=3600):
        """Starts automatic cache refresh in background"""
        self.auto_refresh = True

        def refresh_worker():
            while self.auto_refresh:
                try:
                    print(f"🔄 Refreshing channel cache...")
                    self.channels_cache = None  # Clear cache
                    channels = self.get_channels()
                    print(f"✅ Cache refreshed: {len(channels)} channels")
                except Exception as e:
                    print(f"❌ Cache refresh error: {e}")

                # Wait for specified time
                for _ in range(interval):
                    if not self.auto_refresh:
                        break
                    time.sleep(1)

        self.refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        self.refresh_thread.start()

    def stop_auto_refresh(self):
        """Stops automatic refresh"""
        self.auto_refresh = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5)

class M3UServer(BaseHTTPRequestHandler):
    """Simple HTTP server for serving M3U files"""

    def __init__(self, generator, *args, **kwargs):
        self.generator = generator
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)

            if parsed_path.path == '/playlist.m3u' or parsed_path.path == '/':
                # Parse parameters
                params = parse_qs(parsed_path.query)
                # Use query parameter if provided, otherwise use default setting
                if 'epg' in params:
                    include_epg = params['epg'][0].lower() == 'true'
                else:
                    include_epg = self.generator.default_epg

                print(f"📡 Generating M3U playlist (EPG: {include_epg})...")
                m3u_content = self.generator.generate_m3u(include_epg=include_epg)

                if m3u_content:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.send_header('Content-Disposition', 'attachment; filename="megogo.m3u"')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(m3u_content.encode('utf-8'))
                    print("✅ Playlist sent")
                else:
                    self.send_error(500, "Playlist generation error")

            elif parsed_path.path == '/status':
                # Status endpoint
                channels = self.generator.get_channels()
                status = {
                    'status': 'ok',
                    'channels_count': len(channels),
                    'last_update': datetime.fromtimestamp(self.generator.cache_time).isoformat() if self.generator.cache_time else None
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))

            else:
                self.send_error(404, "Not found")

        except Exception as e:
            print(f"❌ Server error: {e}")
            self.send_error(500, f"Server error: {e}")

    def log_message(self, format, *args):
        """Disable default logging"""
        pass

def create_server_handler(generator):
    """Factory function for server handler"""
    def handler(*args, **kwargs):
        M3UServer(generator, *args, **kwargs)
    return handler

def main():
    parser = argparse.ArgumentParser(description='M3U playlist generator for Megogo')
    parser.add_argument('--output', '-o', help='M3U output file')
    parser.add_argument('--epg', action='store_true', help='Include current program information')
    parser.add_argument('--server', action='store_true', help='Run as HTTP server')
    parser.add_argument('--port', type=int, default=8080, help='HTTP server port (default 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Server IP address (default 0.0.0.0)')
    parser.add_argument('--refresh-interval', type=int, default=3600, help='Cache refresh interval in seconds (default 3600 = 1h)')
    parser.add_argument('--cache-duration', type=int, default=3600, help='Cache lifetime in seconds (default 3600 = 1h)')
    parser.add_argument('--lang', default=None, help='Language for API calls (default from MEGOGO_LANG env or "pl")')

    args = parser.parse_args()

    # Get language from argument, environment variable, or default to 'pl'
    lang = args.lang or os.getenv('MEGOGO_LANG', 'pl')
    
    # Get default EPG setting from environment variable
    default_epg = os.getenv('ENABLE_EPG', 'false').lower() == 'true'
    
    generator = MegogoM3UGenerator(cache_duration=args.cache_duration, lang=lang, default_epg=default_epg)
    
    if args.server:
        # Server mode
        print(f"🚀 Starting M3U server on {args.host}:{args.port}")
        print(f"📺 Playlist available at: http://{args.host}:{args.port}/playlist.m3u")
        print(f"📊 Server status: http://{args.host}:{args.port}/status")
        print(f"💡 Add ?epg=true/false to override EPG setting")
        print(f"🌐 Language: {lang}")
        print(f"📅 Default EPG: {'enabled' if default_epg else 'disabled'}")
        print("⏹️  Press Ctrl+C to stop server")

        # Start automatic refresh if enabled
        if args.refresh_interval > 0:
            print(f"🔄 Automatic refresh every {args.refresh_interval} seconds")
            generator.start_auto_refresh(args.refresh_interval)

        try:
            handler = create_server_handler(generator)
            server = HTTPServer((args.host, args.port), handler)
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Stopping server...")
            generator.stop_auto_refresh()
            server.shutdown()
    else:
        # One-time mode
        if not args.output:
            args.output = f"megogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u"

        result = generator.generate_m3u(include_epg=args.epg, output_file=args.output)
        if result:
            print(f"✅ Done! Playlist saved as: {result}")
        else:
            print("❌ Error generating playlist")
            sys.exit(1)

if __name__ == '__main__':
    main()
