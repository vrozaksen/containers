#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WP Pilot M3U Generator
Simple script to generate M3U playlists from WP Pilot TV service
Based on the Kodi plugin functionality for WP Pilot
"""

import os
import sys
import json
import time
import hashlib
import argparse
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode, quote_plus, quote, unquote
import threading
import random
import base64

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)

# Constants from original Kodi plugin
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
BASE_URL = 'https://pilot.wp.pl/'
DEVICE_TYPE = 'android_tv'
PLATFORM = 'ANDROID_TV'

HEADERS = {
    'referer': BASE_URL,
    'User-Agent': UA,
    'content-type': 'application/json'
}

VOD_URL_PARAMS = {
    'platform': PLATFORM,
    'lang': 'POL'
}

class WPPilotM3UGenerator:
    def __init__(self, cache_duration=3600, username=None, password=None, netvicaptcha=None):
        self.session = requests.Session()
        self.channels_cache = None
        self.cache_time = 0
        self.cache_duration = cache_duration  # Default 1 hour
        self.auto_refresh = False
        self.refresh_thread = None
        self.username = username
        self.password = password
        self.netvicaptcha = netvicaptcha
        self.cookies = {}
        self.logged_in = False
        self.device_uid = self.code_gen(32)
        self.player_token = None
        self.packets = []

    def code_gen(self, x):
        """Generate random code (from original plugin)"""
        base = '0123456789abcdef'
        code = ''
        for i in range(0, x):
            code += base[random.randint(0, 15)]
        return code

    def login(self):
        """Login to WP Pilot service"""
        if not self.username or not self.password or not self.netvicaptcha:
            print("❌ Username, password and netvicaptcha are required for login")
            return False

        try:
            url = f'{BASE_URL}api/v1/user_auth/login?device_type={DEVICE_TYPE}'
            headers = HEADERS.copy()
            headers.update({'Referer': BASE_URL + 'tv/'})

            data = {
                "device": DEVICE_TYPE,
                "login": self.username,
                "password": self.password
            }

            login_cookies = {
                'netvicaptcha': self.netvicaptcha
            }

            resp = self.session.post(url, headers=headers, json=data, cookies=login_cookies)
            resp_json = resp.json()

            if 'error' in resp_json['_meta']:
                error_name = resp_json['_meta']['error']['name']
                if error_name == 'login_incorrect_username_or_password':
                    print("❌ Invalid username or password")
                else:
                    print(f"❌ Login error: {error_name}")
                return False
            else:
                self.cookies = dict(resp.cookies)
                self.logged_in = True
                print("✅ Successfully logged in to WP Pilot")

                # Get user packets
                self.get_packets()
                return True

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def get_packets(self):
        """Get user subscription packets"""
        try:
            headers = HEADERS.copy()
            headers.update({'Referer': BASE_URL + 'tv/'})
            url = f'{BASE_URL}api/v1/package_order?device_type={DEVICE_TYPE}'
            resp = self.session.get(url, headers=headers, cookies=self.cookies).json()

            now = int(time.time())
            self.packets = [r['name'] for r in resp['data'] if r['ends_at'] > now]
            print(f"📦 Available packets: {', '.join(self.packets)}")

        except Exception as e:
            print(f"⚠️  Error fetching packets: {e}")
            self.packets = []

    def relogin(self):
        """Re-login when session expired"""
        print("🔄 Session expired, re-logging in...")
        self.logged_in = False
        self.cookies = {}
        return self.login()

    def get_channels(self):
        """Fetches channel list from WP Pilot"""
        # Channel cache
        if self.channels_cache and (time.time() - self.cache_time) < self.cache_duration:
            return self.channels_cache

        if not self.logged_in:
            if not self.login():
                return []

        try:
            url = f'{BASE_URL}api/v3/channels/list?device_type={DEVICE_TYPE}'
            resp = self.session.get(url, headers=HEADERS, cookies=self.cookies).json()

            if 'error' in resp['_meta']:
                if resp['_meta']['error']['name'] == 'not_authorized':
                    if self.relogin():
                        return self.get_channels()  # Retry after relogin
                    else:
                        return []
                else:
                    print(f"❌ Error fetching channels: {resp['_meta']['error']['name']}")
                    return []
            else:
                # Filter available channels
                channels = [r for r in resp['data'] if r['access_status'] == 'free' or r['access_status'] == 'subscribed']

                self.channels_cache = channels
                self.cache_time = time.time()
                return channels

        except Exception as e:
            print(f"❌ Error fetching channels: {e}")
            return []

    def get_epg(self, channel_ids):
        """Fetches EPG for channels"""
        try:
            import math
            cnt = math.ceil(len(channel_ids) / 20)
            ch_groups = []
            for i in range(0, cnt):
                ch_groups.append(','.join(channel_ids[20*i:20*(i+1)]))

            epg = {}
            for cg in ch_groups:
                url = f'{BASE_URL}api/v2/epg?channels={cg}&limit=12&device_type=web'
                headers = HEADERS.copy()
                headers.update({'Referer': BASE_URL + 'tv/'})
                resp = self.session.get(url, headers=headers, cookies=self.cookies).json()

                for r in resp['data']:
                    progs = ''
                    for e in r['entries']:
                        ts = self.locTime(e['start'])
                        title = e['title']
                        categ = e['category']
                        progs += f'{ts} {title} ({categ})\n'
                    epg[str(r['channel_id'])] = progs.strip()
            return epg

        except Exception as e:
            print(f"⚠️  Error fetching EPG: {e}")
            return {}

    def locTime(self, x):
        """Convert UTC time to local time"""
        import time
        from datetime import datetime, timedelta
        diff = (datetime.now() - datetime.utcnow())
        y = datetime(*(time.strptime(x, '%Y-%m-%dT%H:%M:%SZ')[0:6]))
        z = (y + diff + timedelta(seconds=1)).strftime('%H:%M')
        return z

    def get_stream_url(self, channel_id):
        """Get stream URL for a channel (simplified version)"""
        try:
            # Close any existing stream
            self.close_stream()

            device_type = 'web'
            url = f'{BASE_URL}api/v3/channel/{channel_id}?device_type={device_type}'
            headers = HEADERS.copy()
            headers.update({'Referer': BASE_URL + 'tv/'})

            resp = self.session.get(url, headers=headers, cookies=self.cookies).json()

            if resp['data'] is None:
                if resp['_meta']['error']['code'] == 300:
                    self.close_stream(resp['_meta']['error']['info']['stream_token'])
                    resp = self.session.get(url, headers=headers, cookies=self.cookies).json()
                elif resp['_meta']['error']['name'] == 'not_authorized':
                    if self.relogin():
                        return self.get_stream_url(channel_id)
                    return None
                elif resp['_meta']['error']['name'] == 'user_channel_blocked':
                    print(f"⚠️  Channel {channel_id} temporarily blocked")
                    return None

            if resp['data'] is not None:
                self.player_token = resp['data']['token']

                # Get HLS stream (simpler than DASH with DRM)
                try:
                    stream_url = [r['url'] for r in resp['data']['stream_channel']['streams'] if 'hls' in r['type']][0][0]
                    return stream_url
                except (KeyError, IndexError):
                    print(f"⚠️  No HLS stream found for channel {channel_id}")
                    return None

            return None

        except Exception as e:
            print(f"❌ Error getting stream URL for channel {channel_id}: {e}")
            return None

    def close_stream(self, token=None):
        """Close existing stream"""
        try:
            url = f'{BASE_URL}api/v2/channels/close?device_type={DEVICE_TYPE}'
            headers = HEADERS.copy()
            headers.update({'Referer': BASE_URL + 'tv/'})

            data = {
                'token': token or self.player_token
            }

            if data['token']:
                self.session.post(url, headers=headers, cookies=self.cookies, json=data)

        except Exception as e:
            print(f"⚠️  Error closing stream: {e}")

    def generate_m3u(self, include_epg=False, output_file=None):
        """Generates M3U playlist"""
        print("📺 Fetching channel list from WP Pilot...")
        channels = self.get_channels()

        if not channels:
            print("❌ Failed to fetch channels")
            return None

        print(f"✅ Found {len(channels)} channels")

        # Optionally fetch EPG
        epg = {}
        if include_epg:
            print("📅 Fetching program information...")
            channel_ids = [str(c['id']) for c in channels]
            epg = self.get_epg(channel_ids)

        # Generate M3U
        m3u_content = '#EXTM3U\n'

        for c in channels:
            channel_id = str(c['id'])
            channel_name = c['name']
            channel_logo = c['icon']['dark']

            # Add EPG information to channel name if available
            display_name = channel_name
            if include_epg and channel_id in epg and epg[channel_id]:
                current_program = epg[channel_id].split('\n')[0] if epg[channel_id] else ''
                if current_program:
                    display_name = f"{channel_name} • {current_program}"

            # Get stream URL
            stream_url = self.get_stream_url(channel_id)
            if not stream_url:
                print(f"⚠️  Failed to get stream URL for {channel_name}, skipping...")
                continue

            m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-logo="{channel_logo}" group-title="WP Pilot",{display_name}\n'
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
                include_epg = params.get('epg', ['false'])[0].lower() == 'true'

                print(f"📡 Generating M3U playlist (EPG: {include_epg})...")
                m3u_content = self.generator.generate_m3u(include_epg=include_epg)

                if m3u_content:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.send_header('Content-Disposition', 'attachment; filename="wppilot.m3u"')
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
                    'logged_in': self.generator.logged_in,
                    'channels_count': len(channels),
                    'packets': self.generator.packets,
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
    parser = argparse.ArgumentParser(description='M3U playlist generator for WP Pilot')
    parser.add_argument('--output', '-o', help='M3U output file')
    parser.add_argument('--epg', action='store_true', help='Include current program information')
    parser.add_argument('--server', action='store_true', help='Run as HTTP server')
    parser.add_argument('--port', type=int, default=8080, help='HTTP server port (default 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Server IP address (default 0.0.0.0)')
    parser.add_argument('--refresh-interval', type=int, default=3600, help='Cache refresh interval in seconds (default 3600 = 1h)')
    parser.add_argument('--cache-duration', type=int, default=3600, help='Cache lifetime in seconds (default 3600 = 1h)')
    parser.add_argument('--username', help='WP Pilot username (default from WPPILOT_USERNAME env)')
    parser.add_argument('--password', help='WP Pilot password (default from WPPILOT_PASSWORD env)')
    parser.add_argument('--netvicaptcha', help='netvicaptcha cookie value (default from WPPILOT_NETVICAPTCHA env)')

    args = parser.parse_args()

    # Get credentials from arguments or environment variables
    username = args.username or os.getenv('WPPILOT_USERNAME')
    password = args.password or os.getenv('WPPILOT_PASSWORD')
    netvicaptcha = args.netvicaptcha or os.getenv('WPPILOT_NETVICAPTCHA')

    if not username or not password or not netvicaptcha:
        print("❌ Error: WP Pilot credentials are required!")
        print("   Set them via environment variables:")
        print("   - WPPILOT_USERNAME")
        print("   - WPPILOT_PASSWORD")
        print("   - WPPILOT_NETVICAPTCHA")
        print("   Or use command line arguments --username, --password, --netvicaptcha")
        sys.exit(1)

    generator = WPPilotM3UGenerator(
        cache_duration=args.cache_duration,
        username=username,
        password=password,
        netvicaptcha=netvicaptcha
    )

    if args.server:
        # Server mode
        print(f"🚀 Starting M3U server on {args.host}:{args.port}")
        print(f"📺 Playlist available at: http://{args.host}:{args.port}/playlist.m3u")
        print(f"📊 Server status: http://{args.host}:{args.port}/status")
        print(f"💡 Add ?epg=true/false to override EPG setting")
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
            args.output = f"wppilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u"

        result = generator.generate_m3u(include_epg=args.epg, output_file=args.output)
        if result:
            print(f"✅ Done! Playlist saved as: {result}")
        else:
            print("❌ Error generating playlist")
            sys.exit(1)

if __name__ == '__main__':
    main()
