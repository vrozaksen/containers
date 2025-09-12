#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Megogo M3U Generator
Script to generate M3U playlists from Megogo.net channels with direct stream URLs
Compatible with any IPTV player (Emby, Jellyfin, VLC, etc.)
Supports device authentication and full API access
"""

import os
import sys
import json
import time
import hashlib
import argparse
import random
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import threading

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)

# Constants from Megogo API (Android TV version)
UA = 'Dalvik/2.1.0 (Linux; U; Android 8.0.0; Unknown sdk_google_atv_x86; Build/OSR1.180418.025)'
API_URL = 'https://api.megogo.net/v1/'

# API keys from Megogo Android TV app (ver 2.11.6)
APIS = {
    'true': ['a3a854fdd3', '_android_tv_drm_4k_17'],   # with DRM
    'false': ['2901c3d95c', '_android_tv_4k_17']        # without DRM
}

# Headers for API requests
HEADERS = {
    'x-client-type': 'AndroidTV',
    'x-client-version': '2.11.6',
    'user-agent': UA,
    'device-name': 'Unknown sdk_google_atv_x86',
    'device-model': 'sdk_google_atv_x86',
    'accept-encoding': 'gzip'
}

def code_gen(length, only_digit=False):
    """Generate random code"""
    base = '0123456789abcdef' if not only_digit else '0123456789'
    count = 15 if not only_digit else 9
    code = ''
    for i in range(0, length):
        code += base[random.randint(0, count)]
    return code

def get_sign(params, drm_support='false'):
    """Generate API signature"""
    s = ''.join([k + '=' + str(params[k]) for k in params.keys()])
    s += APIS[drm_support][0]  # private_key
    s_hash = hashlib.md5(s.encode('utf-8')).hexdigest()
    s_hash += APIS[drm_support][1]  # public_key
    return s_hash

class MegogoM3UGenerator:
    def __init__(self, cache_duration=3600, lang='pl', default_epg=False, drm_support='false',
                 config_file=None, geo_zone='UA'):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # Cache settings
        self.channels_cache = None
        self.cache_time = 0
        self.cache_duration = cache_duration
        self.auto_refresh = False
        self.refresh_thread = None

        # API settings
        self.lang = lang
        self.default_epg = default_epg
        self.drm_support = drm_support
        self.geo_zone = geo_zone

        # Authentication data
        self.device_id = None
        self.access_token = None
        self.access_token_exp = 0
        self.remember_me_token = None
        self.access_key = None
        self.user_id = None
        self.logged_in = False

        # Config file for persistent storage
        self.config_file = config_file or 'megogo_config.json'
        self.load_config()

        # Generate device ID if not exists
        if not self.device_id:
            self.device_id = 'ANDROIDTV' + code_gen(10, True) + '__' + code_gen(16)
            self.save_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.device_id = config.get('device_id')
                    self.access_token = config.get('access_token')
                    self.access_token_exp = config.get('access_token_exp', 0)
                    self.remember_me_token = config.get('remember_me_token')
                    self.access_key = config.get('access_key')
                    self.user_id = config.get('user_id')
                    self.logged_in = config.get('logged_in', False)
                    print(f"✅ Configuration loaded from {self.config_file}")
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'device_id': self.device_id,
                'access_token': self.access_token,
                'access_token_exp': self.access_token_exp,
                'remember_me_token': self.remember_me_token,
                'access_key': self.access_key,
                'user_id': self.user_id,
                'logged_in': self.logged_in
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")

    def req(self, method, url, params=None, data=None, cookies=None):
        """Make API request with automatic token refresh"""
        if self.logged_in:
            now = int(time.time())
            if self.access_token_exp - now <= 10 * 60:  # Refresh if expires in 10 minutes
                if not self.refresh_tokens():
                    return None

                # Update params with new token
                if params and 'access_token' in params:
                    params['access_token'] = self.access_token
                    # Regenerate signature
                    if 'sign' in params:
                        del params['sign']
                        params['sign'] = get_sign(params, self.drm_support)

        try:
            if method == 'get':
                resp = self.session.get(url, params=params, cookies=cookies, timeout=10)
            elif method == 'post':
                resp = self.session.post(url, params=params, data=data, json=data if isinstance(data, dict) else None, cookies=cookies, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return resp.json()
        except Exception as e:
            print(f"❌ API request error: {e}")
            return None

    def login_with_device_code(self):
        """Login using device code (like TV devices)"""
        print("🔐 Starting device authentication...")

        # Step 1: Get device code
        url = API_URL + 'device/code'
        params = {
            'device_name': 'Device_' + code_gen(3, True),
            'lang': self.lang,
            'did': self.device_id
        }
        params['sign'] = get_sign(params, self.drm_support)

        resp = self.req('get', url, params=params)
        if not resp or resp.get('result') != 'ok':
            print(f"❌ Error getting device code: {resp}")
            return False

        code = resp['data']['code']
        print(f"📱 Go to https://megogo.net/device and enter code: {code}")
        print("⏳ Waiting for authentication... (Press Ctrl+C to cancel)")

        # Step 2: Wait for user to enter code and authenticate
        max_attempts = 60  # Wait up to 5 minutes
        for attempt in range(max_attempts):
            try:
                time.sleep(5)  # Check every 5 seconds

                url = API_URL + 'auth/user'
                params = {
                    'did': self.device_id,
                    'lang': self.lang
                }
                params['sign'] = get_sign(params, self.drm_support)

                resp = self.req('get', url, params=params)
                if resp and resp.get('result') == 'ok':
                    # Authentication successful
                    data = resp.get('data', {})
                    if 'user' in data:
                        user_data = data['user']
                        self.access_token = user_data['tokens']['access_token']
                        self.access_token_exp = user_data['tokens']['access_token_expires_at']
                        self.remember_me_token = user_data['tokens']['remember_me_token']
                        self.access_key = user_data['extra']['access_key']
                        self.user_id = str(user_data['user_id'])
                        self.logged_in = True

                        self.save_config()
                        print("✅ Authentication successful!")
                        return True
                    else:
                        # Debug: print response structure to understand it better
                        print(f"🔍 Debug: Response data keys: {list(data.keys()) if data else 'No data'}")
                        if attempt % 6 == 0:  # Print every 30 seconds
                            print(f"⏳ Still waiting for authentication... (attempt {attempt + 1}/{max_attempts})")
                elif resp:
                    # For debugging purposes, show what we're getting
                    if attempt % 6 == 0:  # Print every 30 seconds
                        print(f"🔍 Debug: API response: {resp}")
                        print(f"⏳ Still waiting for authentication... (attempt {attempt + 1}/{max_attempts})")

            except KeyboardInterrupt:
                print("\n❌ Authentication cancelled by user")
                return False
            except Exception as e:
                print(f"⚠️  Authentication check error: {e}")

        print("❌ Authentication timeout")
        return False

    def refresh_tokens(self):
        """Refresh access tokens"""
        if not self.user_id:
            return False

        url = API_URL + 'auth/user_token'
        params = {
            'user_id': self.user_id,
            'lang': self.lang,
            'did': self.device_id
        }
        params['sign'] = get_sign(params, self.drm_support)

        resp = self.req('get', url, params=params)
        if resp and resp.get('result') == 'ok':
            self.access_token = resp['data']['tokens']['access_token']
            self.access_token_exp = resp['data']['tokens']['access_token_expires_at']
            self.remember_me_token = resp['data']['tokens']['remember_me_token']
            self.access_key = resp['data']['extra']['access_key']
            self.save_config()
            print("🔄 Tokens refreshed successfully")
            return True
        else:
            print("❌ Token refresh failed")
            self.logout()
            return False

    def logout(self):
        """Logout and clear tokens"""
        if self.logged_in:
            url = API_URL + 'auth/logout'
            params = {
                'lang': self.lang,
                'did': self.device_id
            }
            if self.access_token:
                params['access_token'] = self.access_token
            params['sign'] = get_sign(params, self.drm_support)

            self.req('get', url, params=params)

        # Clear all authentication data
        self.access_token = None
        self.access_token_exp = 0
        self.remember_me_token = None
        self.access_key = None
        self.user_id = None
        self.logged_in = False
        self.save_config()
        print("👋 Logged out successfully")

    def get_channels(self):
        """Fetches channel list from Megogo API"""
        # Check cache
        if self.channels_cache and (time.time() - self.cache_time) < self.cache_duration:
            return self.channels_cache

        try:
            url = API_URL + 'tv/channels'
            params = {
                'lang': self.lang,
            }
            if self.logged_in and self.access_token:
                params['access_token'] = self.access_token
            params['sign'] = get_sign(params, self.drm_support)

            resp = self.req('get', url, params=params)
            if not resp or resp.get('result') != 'ok':
                print(f"❌ Error fetching channels: {resp}")
                return []

            channels = resp['data']['channels']

            # Filter available non-VOD channels
            available_channels = []
            for c in channels:
                if not c['vod_channel'] and c['is_available']:
                    available_channels.append(c)

            self.channels_cache = available_channels
            self.cache_time = time.time()
            print(f"✅ Found {len(available_channels)} available channels")
            return available_channels

        except Exception as e:
            print(f"❌ Error fetching channels: {e}")
            return []

    def get_epg_live(self, channel_ids):
        """Fetches current program for channels"""
        try:
            since = int(time.time())
            till = since + 8 * 60 * 60

            url = API_URL + 'epg'
            params = {
                'channel_id': channel_ids,
                'from': str(since),
                'to': str(till),
                'lang': self.lang,
            }
            if self.logged_in and self.access_token:
                params['access_token'] = self.access_token
            params['sign'] = get_sign(params, self.drm_support)

            resp = self.req('get', url, params=params)
            if not resp or resp.get('result') != 'ok':
                print(f"⚠️  Error fetching EPG: {resp}")
                return {}

            chans = resp['data']
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

    def get_stream_url(self, channel_id):
        """Get stream URL for a channel"""
        try:
            url = API_URL + 'stream'
            params = {
                'video_id': channel_id,
                'lang': self.lang,
                'did': self.device_id
            }
            if self.logged_in and self.access_token:
                params['access_token'] = self.access_token
            params['sign'] = get_sign(params, self.drm_support)

            resp = self.req('get', url, params=params)
            if resp and resp.get('result') == 'ok':
                stream_data = resp['data']
                if 'bitrates' in stream_data and stream_data['bitrates']:
                    # Get highest quality stream
                    bitrates = sorted(stream_data['bitrates'], key=lambda x: x.get('bitrate', 0), reverse=True)
                    return bitrates[0]['src']
                elif 'src' in stream_data:
                    return stream_data['src']

            # Fallback - return None if no stream available
            return None

        except Exception as e:
            print(f"⚠️  Error getting stream URL for channel {channel_id}: {e}")
            return None

    def generate_m3u(self, include_epg=False, output_file=None):
        """Generates M3U playlist with direct stream URLs"""
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
        successful_channels = 0

        for c in channels:
            channel_id = str(c['id'])
            channel_name = c['title']
            channel_logo = c['image']['original']

            # Check if it's radio or TV based on genres
            is_radio = False
            if 'genres' in c and c['genres']:
                # Genre ID 40625 is typically for radio channels
                is_radio = 40625 in c['genres']

            group_title = "Megogo Radio" if is_radio else "Megogo TV"

            # Add EPG information to channel name if available
            display_name = channel_name
            if include_epg and channel_id in epg and epg[channel_id]:
                current_program = epg[channel_id].split('\n')[0] if epg[channel_id] else ''
                if current_program:
                    display_name = f"{channel_name} • {current_program}"

            # Get direct stream URL
            print(f"🔗 Getting stream URL for {channel_name}...")
            stream_url = self.get_stream_url(channel_id)

            if stream_url:
                successful_channels += 1
                # Add channel entry to M3U
                if c.get('is_dvr', False):
                    # Channel supports catchup/timeshift
                    m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-logo="{channel_logo}" group-title="{group_title}" catchup="append" catchup-source="&s={{utc:Y-m-dTH:M:S}}&e={{utcend:Y-m-dTH:M:S}}" catchup-days="7",{display_name}\n'
                else:
                    m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-logo="{channel_logo}" group-title="{group_title}",{display_name}\n'

                m3u_content += f"{stream_url}\n"
            else:
                print(f"⚠️  Skipping {channel_name} - no stream URL available")

        print(f"✅ Successfully processed {successful_channels} channels with stream URLs")

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

                # EPG setting
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
                    'last_update': datetime.fromtimestamp(self.generator.cache_time).isoformat() if self.generator.cache_time else None,
                    'authenticated': self.generator.logged_in,
                    'device_id': self.generator.device_id,
                    'language': self.generator.lang,
                    'drm_support': self.generator.drm_support
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
    parser = argparse.ArgumentParser(description='M3U playlist generator for Megogo with device authentication')
    parser.add_argument('--output', '-o', help='M3U output file')
    parser.add_argument('--epg', action='store_true', help='Include current program information')
    parser.add_argument('--server', action='store_true', help='Run as HTTP server')
    parser.add_argument('--port', type=int, default=8080, help='HTTP server port (default 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Server IP address (default 0.0.0.0)')
    parser.add_argument('--refresh-interval', type=int, default=3600, help='Cache refresh interval in seconds (default 3600 = 1h)')
    parser.add_argument('--cache-duration', type=int, default=3600, help='Cache lifetime in seconds (default 3600 = 1h)')
    parser.add_argument('--lang', default=None, help='Language for API calls (default from MEGOGO_LANG env or "pl")')
    parser.add_argument('--login', action='store_true', help='Login with device code')
    parser.add_argument('--logout', action='store_true', help='Logout and clear stored credentials')
    parser.add_argument('--config', help='Configuration file path (default: megogo_config.json)')
    parser.add_argument('--drm', action='store_true', help='Enable DRM support')

    parser.add_argument('--geo-zone', default='UA', help='Geographic zone (default: UA)')

    args = parser.parse_args()

    # Get language from argument, environment variable, or default to 'pl'
    lang = args.lang or os.getenv('MEGOGO_LANG', 'pl')

    # Get default EPG setting from environment variable
    default_epg = os.getenv('ENABLE_EPG', 'false').lower() == 'true'

    # DRM support
    drm_support = 'true' if args.drm else 'false'

    generator = MegogoM3UGenerator(
        cache_duration=args.cache_duration,
        lang=lang,
        default_epg=default_epg,
        drm_support=drm_support,
        config_file=args.config,
        geo_zone=args.geo_zone
    )

    # Handle authentication commands
    if args.logout:
        generator.logout()
        return

    if args.login:
        if generator.login_with_device_code():
            print("✅ Login successful! You can now generate playlists.")
        else:
            print("❌ Login failed!")
            sys.exit(1)
        return

    # Check if authentication is needed
    if not generator.logged_in:
        print("⚠️  You are not logged in. Some channels might not be available.")
        print("💡 Use --login to authenticate with device code")
        print("   Or run the script in server mode and it will work with available free channels")

    if args.server:
        # Server mode
        print(f"🚀 Starting M3U server on {args.host}:{args.port}")
        print(f"📺 Playlist available at: http://{args.host}:{args.port}/playlist.m3u")
        print(f"📊 Server status: http://{args.host}:{args.port}/status")
        print(f"💡 Add ?epg=true/false to override EPG setting")
        print(f"🌐 Language: {lang}")
        print(f"📅 Default EPG: {'enabled' if default_epg else 'disabled'}")
        print(f"🔐 Authentication: {'logged in' if generator.logged_in else 'not logged in'}")
        print(f"🔒 DRM Support: {'enabled' if drm_support == 'true' else 'disabled'}")
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
            if generator.logged_in:
                print("🔐 Used authenticated access - all available channels included")
            else:
                print("⚠️  Used guest access - only free channels included")
        else:
            print("❌ Error generating playlist")
            sys.exit(1)

if __name__ == '__main__':
    main()
