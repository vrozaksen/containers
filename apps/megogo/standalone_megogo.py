#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Megogo M3U Generator
A simple script to generate M3U playlists from Megogo without Docker

Usage:
    python3 standalone_megogo.py --email your@email.com --password yourpassword
    python3 standalone_megogo.py --config  # Interactive configuration
"""

import os
import sys
import json
import time
import random
import hashlib
import argparse
import getpass
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)

# Constants from original plugin
UA = 'Dalvik/2.1.0 (Linux; U; Android 8.0.0; Unknown sdk_google_atv_x86; Build/OSR1.180418.025)'
API_URL = 'https://api.megogo.net/v1/'

APIS = {
    'true': ['a3a854fdd3', '_android_tv_drm_4k_17'],
    'false': ['2901c3d95c', '_android_tv_4k_17']
}

HEADERS = {
    'x-client-type': 'AndroidTV',
    'x-client-version': '2.11.6',
    'user-agent': UA,
    'device-name': 'Unknown sdk_google_atv_x86',
    'device-model': 'sdk_google_atv_x86',
    'accept-encoding': 'gzip'
}

class StandaloneMegogoClient:
    def __init__(self, config_file='megogo_config.json'):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        default_config = {
            'logged': False,
            'access_token': '',
            'access_token_exp': '',
            'remember_me_token': '',
            'access_key': '',
            'user_id': '',
            'did': self.generate_device_id(),
            'lang': 'pl',
            'geo_zone': 'PL',
            'drm_support': 'false'
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"⚠️ Warning: Could not load config: {e}")
            self.config = default_config

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Could not save config: {e}")

    def generate_device_id(self):
        return 'ANDROIDTV' + self.code_gen(10, True) + '__' + self.code_gen(16)

    def code_gen(self, length, only_digit=False):
        base = '0123456789abcdef' if not only_digit else '0123456789'
        count = 15 if not only_digit else 9
        return ''.join(base[random.randint(0, count)] for _ in range(length))

    def get_sign(self, params):
        is_drm = self.config['drm_support']
        s = ''.join([f"{k}={params[k]}" for k in params.keys()])
        s += APIS[is_drm][0]
        s_hash = hashlib.md5(s.encode('utf-8')).hexdigest()
        s_hash += APIS[is_drm][1]
        return s_hash

    def api_request(self, endpoint, params=None, method='GET'):
        if params is None:
            params = {}

        params.update({
            'lang': self.config['lang'],
            'did': self.config['did']
        })

        if self.config['logged']:
            params['access_token'] = self.config['access_token']

        params['sign'] = self.get_sign(params)

        url = API_URL + endpoint

        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            else:
                response = requests.post(url, headers=HEADERS, data=params, timeout=30)

            return response.json()
        except Exception as e:
            print(f"❌ API request failed: {e}")
            return {'result': 'error', 'error': str(e)}

    def login(self, email, password):
        print(f"🔐 Logging in to Megogo...")

        params = {
            'login': email,
            'password': password,
            'remember': '1',
            'did': self.config['did'],
            'lang': self.config['lang']
        }

        headers = {**HEADERS, 'Content-Type': 'application/x-www-form-urlencoded'}
        params['sign'] = self.get_sign(params)

        try:
            response = requests.post(API_URL + 'auth/login/email', headers=headers, data=params)
            result = response.json()

            if result.get('result') == 'ok':
                user_data = result['data']['user']
                self.config.update({
                    'logged': True,
                    'access_token': user_data['tokens']['access_token'],
                    'access_token_exp': str(user_data['tokens']['access_token_expires_at']),
                    'remember_me_token': user_data['tokens']['remember_me_token'],
                    'access_key': user_data['extra']['access_key'],
                    'user_id': str(user_data['user_id'])
                })
                self.save_config()
                print("✅ Login successful!")
                return True
            else:
                error_msg = result.get('error', result.get('data', {}).get('error', 'Login failed'))
                print(f"❌ Login failed: {error_msg}")
                return False
        except Exception as e:
            print(f"❌ Network error during login: {e}")
            return False

    def get_channels(self):
        print("📺 Fetching channel list...")
        result = self.api_request('tv/channels')
        if result.get('result') == 'ok':
            channels = result['data']['channels']
            live_channels = [c for c in channels if not c['vod_channel'] and c['is_available']]
            print(f"✅ Found {len(live_channels)} live channels")
            return channels
        else:
            print(f"❌ Failed to get channels: {result.get('error', 'Unknown error')}")
            return []

    def generate_m3u(self, output_file='megogo_playlist.m3u', include_logos=True):
        if not self.config['logged']:
            print("❌ Please login first!")
            return False

        print("🎬 Generating M3U playlist...")
        channels = self.get_channels()

        if not channels:
            print("❌ No channels available")
            return False

        m3u_content = '#EXTM3U\n'
        live_channel_count = 0

        for channel in channels:
            if not channel['vod_channel'] and channel['is_available']:
                name = channel['title']
                logo = channel['image']['original'] if include_logos else ''
                channel_id = channel['id']

                # For standalone use, we can't proxy streams, so we'd need direct URLs
                # This is a limitation - you might need to implement a simple HTTP server
                # For now, we'll create placeholder URLs
                stream_url = f"http://localhost:8080/stream/{channel_id}"

                logo_attr = f' tvg-logo="{logo}"' if logo else ''

                if channel.get('is_dvr'):
                    m3u_content += f'#EXTINF:0 tvg-id="{channel_id}" tvg-name="{name}"{logo_attr} group-title="Megogo Live" catchup="append" catchup-source="&s={{utc:Y-m-dTH:M:S}}&e={{utcend:Y-m-dTH:M:S}}" catchup-days="7",{name}\n{stream_url}\n'
                else:
                    m3u_content += f'#EXTINF:0 tvg-id="{channel_id}" tvg-name="{name}"{logo_attr} group-title="Megogo Live",{name}\n{stream_url}\n'

                live_channel_count += 1

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(m3u_content)

            print(f"✅ M3U playlist generated: {output_file}")
            print(f"📊 Channels included: {live_channel_count}")
            print(f"⚠️  Note: This playlist requires the Docker service or a proxy server to work with media players")
            return True
        except Exception as e:
            print(f"❌ Failed to write M3U file: {e}")
            return False

    def interactive_config(self):
        print("⚙️ Interactive Configuration")
        print("=" * 40)

        # Email and password
        email = input("📧 Megogo email: ").strip()
        password = getpass.getpass("🔒 Megogo password: ")

        # Language
        current_lang = self.config.get('lang', 'pl')
        lang = input(f"🌍 Language [{current_lang}]: ").strip() or current_lang

        # Geo zone
        current_geo = self.config.get('geo_zone', 'PL')
        geo_zone = input(f"🗺️  Geographic zone [{current_geo}]: ").strip() or current_geo

        # Update config
        self.config['lang'] = lang
        self.config['geo_zone'] = geo_zone
        self.save_config()

        # Attempt login
        if self.login(email, password):
            # Generate M3U
            include_logos = input("🖼️  Include channel logos? [Y/n]: ").strip().lower() not in ['n', 'no']
            output_file = input("📁 Output filename [megogo_playlist.m3u]: ").strip() or "megogo_playlist.m3u"

            self.generate_m3u(output_file, include_logos)

        return self.config['logged']

def main():
    parser = argparse.ArgumentParser(description='Standalone Megogo M3U Generator')
    parser.add_argument('--email', help='Megogo email address')
    parser.add_argument('--password', help='Megogo password')
    parser.add_argument('--output', '-o', default='megogo_playlist.m3u', help='Output M3U filename')
    parser.add_argument('--config', action='store_true', help='Interactive configuration')
    parser.add_argument('--no-logos', action='store_true', help='Exclude channel logos')
    parser.add_argument('--lang', default='pl', help='Language code (e.g., pl, en, ua)')
    parser.add_argument('--geo-zone', default='PL', help='Geographic zone (e.g., PL, UA)')

    args = parser.parse_args()

    print("🎬 Standalone Megogo M3U Generator")
    print("=" * 40)

    client = StandaloneMegogoClient()

    # Update config with command line args
    client.config['lang'] = args.lang
    client.config['geo_zone'] = args.geo_zone
    client.save_config()

    if args.config:
        # Interactive mode
        success = client.interactive_config()
    elif args.email and args.password:
        # Command line mode
        success = client.login(args.email, args.password)
        if success:
            client.generate_m3u(args.output, not args.no_logos)
    else:
        # Check if already logged in
        if client.config['logged']:
            print("✅ Already logged in, generating playlist...")
            client.generate_m3u(args.output, not args.no_logos)
        else:
            print("❌ Please provide email and password, or use --config for interactive mode")
            print("Example: python3 standalone_megogo.py --email your@email.com --password yourpassword")
            sys.exit(1)

    if client.config['logged']:
        print("\n📝 Next steps:")
        print("1. Start the Docker service for stream proxying:")
        print("   docker run -d -p 8080:8080 ghcr.io/vrozaksen/megogo:latest")
        print("2. Use the generated M3U file in your media player")
        print("3. Or use the web interface at http://localhost:8080")

if __name__ == "__main__":
    main()
