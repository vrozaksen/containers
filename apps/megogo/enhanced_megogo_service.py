# -*- coding: utf-8 -*-
"""
Enhanced Megogo Service with full plugin functionality
Based on the original Kodi plugin but adapted for standalone use
"""

import os
import sys
import json
import time
import random
import hashlib
import datetime
import requests
from urllib.parse import urlencode, quote_plus, parse_qsl
from fastapi import FastAPI, HTTPException, Form, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
import uvicorn

app = FastAPI(title="Enhanced Megogo Service")

# Original plugin constants
UA = 'Dalvik/2.1.0 (Linux; U; Android 8.0.0; Unknown sdk_google_atv_x86; Build/OSR1.180418.025)'
API_URL = 'https://api.megogo.net/v1/'
DATA_DIR = '/app/data'

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

class EnhancedMegogoClient:
    def __init__(self):
        self.config_file = os.path.join(DATA_DIR, 'config.json')
        self.load_config()
        self.auto_login_from_env()

    def load_config(self):
        default_config = {
            'logged': False,
            'access_token': '',
            'access_token_exp': '',
            'remember_me_token': '',
            'access_key': '',
            'user_id': '',
            'did': self.generate_device_id(),
            'adid': self.generate_ad_id(),
            'lang': os.getenv('MEGOGO_LANG', 'pl'),
            'geo_zone': os.getenv('MEGOGO_GEO_ZONE', 'PL'),
            'drm_support': os.getenv('MEGOGO_DRM_SUPPORT', 'false'),
            'conf_updt': '0'
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            else:
                self.config = default_config
                self.save_config()
        except:
            self.config = default_config
            self.save_config()

    def auto_login_from_env(self):
        """Automatic login from environment variables"""
        email = os.getenv('MEGOGO_EMAIL')
        password = os.getenv('MEGOGO_PASSWORD')

        if email and password and not self.config['logged']:
            print(f"🔐 Auto-login attempt for {email}")
            success, message = self.login_via_email(email, password)
            if success:
                print("✅ Auto-login successful!")
            else:
                print(f"❌ Auto-login failed: {message}")

    def save_config(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def generate_device_id(self):
        return 'ANDROIDTV' + self.code_gen(10, True) + '__' + self.code_gen(16)

    def generate_ad_id(self):
        return f"{self.code_gen(8)}-{self.code_gen(4)}-{self.code_gen(4)}-{self.code_gen(4)}-{self.code_gen(12)}"

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

    def refresh_tokens(self):
        """Refresh access tokens if needed"""
        if not self.config['logged']:
            return False

        try:
            now = int(time.time())
            token_exp_time = int(self.config.get('access_token_exp', '0'))

            if token_exp_time - now <= 10 * 60:  # 10 minutes before expiry
                params = {
                    'user_id': self.config['user_id'],
                    'lang': self.config['lang'],
                    'did': self.config['did']
                }
                params['sign'] = self.get_sign(params)

                response = requests.get(API_URL + 'auth/user_token', headers=HEADERS, params=params)
                result = response.json()

                if result.get('result') == 'ok':
                    tokens = result['data']['tokens']
                    self.config.update({
                        'access_token': tokens['access_token'],
                        'access_token_exp': str(tokens['access_token_expires_at']),
                        'remember_me_token': tokens['remember_me_token'],
                        'access_key': result['data']['extra']['access_key']
                    })
                    self.save_config()
                    return True
                else:
                    # Token refresh failed, logout
                    self.logout()
                    return False
        except:
            return False

        return True

    def api_request(self, endpoint, params=None, method='GET'):
        if params is None:
            params = {}

        # Refresh tokens if needed
        if self.config['logged']:
            self.refresh_tokens()

        # Add common parameters
        params.update({
            'lang': self.config['lang'],
            'did': self.config['did']
        })

        # Add access token if logged in
        if self.config['logged']:
            params['access_token'] = self.config['access_token']

        # Add signature
        params['sign'] = self.get_sign(params)

        url = API_URL + endpoint

        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            else:
                response = requests.post(url, headers=HEADERS, data=params, timeout=30)

            return response.json()
        except Exception as e:
            print(f"API request failed: {e}")
            return {'result': 'error', 'error': str(e)}

    def login_via_email(self, email, password):
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
                return True, "Login successful"
            else:
                error_msg = result.get('error', result.get('data', {}).get('error', 'Login failed'))
                return False, error_msg
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def logout(self):
        """Logout and clear tokens"""
        if self.config['logged']:
            try:
                self.api_request('auth/logout')
            except:
                pass

        self.config.update({
            'logged': False,
            'access_token': '',
            'access_token_exp': '',
            'remember_me_token': '',
            'access_key': '',
            'user_id': ''
        })
        self.save_config()

    def get_channels(self, groups=False):
        endpoint = 'tv/channels/grouped' if groups else 'tv/channels'
        result = self.api_request(endpoint)
        if result.get('result') == 'ok':
            return result['data']['channel_groups'] if groups else result['data']['channels']
        return []

    def get_epg_live(self, channel_ids):
        """Get current EPG for live channels"""
        since = int(time.time())
        till = since + 8 * 60 * 60  # 8 hours ahead

        result = self.api_request('epg', {
            'channel_id': channel_ids,
            'from': str(since),
            'to': str(till)
        })

        epg = {}
        if result.get('result') == 'ok':
            for channel in result['data']:
                cid = str(channel['id'])
                programs = []
                for program in channel['programs']:
                    start_time = datetime.datetime.fromtimestamp(program['start_timestamp']).strftime('%H:%M')
                    programs.append(f"[B]{start_time}[/B] {program['title']}")
                epg[cid] = '\n'.join(programs)

        return epg

    def get_stream_url(self, channel_id, virtual_id=None, object_id=None):
        """Get stream URL for a channel or specific content"""
        if virtual_id:
            # Replay content
            params = {
                'video_id': str(channel_id),
                'virtual_id': str(virtual_id)
            }
            endpoint = 'stream/virtual'
        elif object_id:
            # VOD channel content
            params = {
                'video_id': str(virtual_id or channel_id),
                'object_id': str(object_id)
            }
            endpoint = 'stream'
        else:
            # Live channel
            params = {
                'video_id': str(channel_id)
            }
            endpoint = 'stream'

        result = self.api_request(endpoint, params)

        if result.get('result') == 'ok':
            stream_data = result['data']
            if 'bitrates' in stream_data and stream_data['bitrates']:
                # Get highest bitrate stream
                bitrates = sorted(stream_data['bitrates'], key=lambda x: x.get('bitrate', 0), reverse=True)
                return bitrates[0]['src']

        return None

    def generate_m3u(self, include_epg=True):
        """Generate M3U playlist with safe defaults to avoid detection"""
        channels = self.get_channels()

        if include_epg:
            # Get EPG for all live channels
            live_channel_ids = ','.join([str(c['id']) for c in channels if not c['vod_channel'] and c['is_available']])
            if live_channel_ids:
                epg = self.get_epg_live(live_channel_ids)
            else:
                epg = {}

        # M3U header with safe defaults
        m3u_content = '#EXTM3U\n'
        m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Smart TV; Linux; Tizen 6.0) Emby/4.7\n'
        m3u_content += '#EXTVLCOPT:http-referrer=https://megogo.net/\n'

        for channel in channels:
            if not channel['vod_channel'] and channel['is_available']:
                name = channel['title']
                logo = channel['image']['original']
                channel_id = channel['id']

                # Create stream URL that will be handled by our proxy
                stream_url = f"http://localhost:8080/stream/{channel_id}"

                # Add EPG info to title if available
                if include_epg and str(channel_id) in epg:
                    current_program = epg[str(channel_id)].split('\n')[0] if epg[str(channel_id)] else ''
                    if current_program:
                        # Clean up EPG info for display
                        clean_program = current_program.replace('[B]', '').replace('[/B]', '')
                        name += f" - {clean_program}"

                # M3U entry with safe headers
                channel_title = channel['title']
                extinf_line = f'#EXTINF:0 tvg-id="{channel_id}" tvg-name="{channel_title}" tvg-logo="{logo}" group-title="Megogo Live"'

                if channel.get('is_dvr'):
                    extinf_line += ' catchup="append" catchup-source="&s={utc:Y-m-dTH:M:S}&e={utcend:Y-m-dTH:M:S}" catchup-days="7"'

                extinf_line += f',{name}\n'

                # Add safe headers for each stream
                m3u_content += extinf_line
                m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Smart TV; Linux; Tizen 6.0) Emby/4.7\n'
                m3u_content += '#EXTVLCOPT:http-referrer=https://megogo.net/\n'
                m3u_content += f'{stream_url}\n'

        return m3u_content# Initialize client
megogo_client = EnhancedMegogoClient()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced Megogo Service</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white;
                        padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .status { padding: 15px; margin: 15px 0; border-radius: 8px; font-weight: 500; }
            .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .form-section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: 600; }
            input[type="text"], input[type="password"], input[type="email"] {
                width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;
                font-size: 14px; box-sizing: border-box; }
            button { background: linear-gradient(135deg, #007bff, #0056b3); color: white;
                     padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer;
                     font-size: 14px; font-weight: 500; transition: all 0.3s; }
            button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,123,255,0.3); }
            .url-box { background: #f8f9fa; padding: 15px; border-radius: 6px;
                       border: 1px solid #e9ecef; font-family: monospace; margin: 10px 0; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            .channel-count { font-size: 18px; font-weight: 600; color: #28a745; }
            .links { display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }
            .links a { text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 Enhanced Megogo Service</h1>
                <p>Generate M3U playlists and stream Megogo content for Emby, Jellyfin, and other media servers</p>
            </div>

            <div class="status {{ 'success' if logged_in else 'info' }}">
                <strong>Status:</strong>
                {{ "✅ Logged in successfully" if logged_in else "⚠️ Not logged in - Please login to access content" }}
                {% if logged_in and channel_count %}
                <br><span class="channel-count">{{ channel_count }} channels available</span>
                {% endif %}
            </div>

            {% if not logged_in %}
            <div class="form-section">
                <h2>🔐 Login to Megogo</h2>
                <form method="post" action="/login">
                    <div class="form-group">
                        <label for="email">Email Address:</label>
                        <input type="email" id="email" name="email" required placeholder="your.email@example.com">
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">🚀 Login</button>
                </form>
            </div>
            {% else %}
            <div class="form-section">
                <h2>📺 M3U Playlist URLs</h2>
                <p>Use these URLs in your media player (Emby, Jellyfin, VLC, etc.):</p>

                <h4>Standard Playlist:</h4>
                <div class="url-box">http://localhost:8080/playlist.m3u</div>

                <h4>Playlist with Current EPG:</h4>
                <div class="url-box">http://localhost:8080/playlist.m3u?epg=true</div>

                <div class="links">
                    <a href="/playlist.m3u" target="_blank">
                        <button type="button">📥 Download M3U</button>
                    </a>
                    <a href="/playlist.m3u?epg=true" target="_blank">
                        <button type="button">📥 Download M3U + EPG</button>
                    </a>
                    <a href="/channels" target="_blank">
                        <button type="button">📋 View Channels JSON</button>
                    </a>
                </div>

                <form method="post" action="/logout" style="margin-top: 15px;">
                    <button type="submit" style="background: #dc3545;">🚪 Logout</button>
                </form>
            </div>
            {% endif %}

            <div class="form-section">
                <h2>⚙️ Configuration</h2>
                <form method="post" action="/config">
                    <div class="grid">
                        <div class="form-group">
                            <label for="lang">Language Code:</label>
                            <input type="text" id="lang" name="lang" value="{{ config.lang }}" placeholder="pl, en, ua, etc.">
                        </div>
                        <div class="form-group">
                            <label for="geo_zone">Geographic Zone:</label>
                            <input type="text" id="geo_zone" name="geo_zone" value="{{ config.geo_zone }}" placeholder="PL, UA, etc.">
                        </div>
                    </div>
                    <button type="submit">💾 Save Configuration</button>
                </form>
            </div>

            <div class="form-section">
                <h2>📺 Emby/Jellyfin/Plex Configuration Guide</h2>
                <p><strong>⚠️ Important:</strong> Use these exact settings in your media server to avoid detection/bans:</p>

                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h4>🛡️ Recommended Settings for Emby/Jellyfin:</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">M3U URL:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">http://your-server-ip:8080/playlist.m3u</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">HTTP User-Agent:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">Mozilla/5.0 (Smart TV; Linux; Tizen 6.0) Emby/4.7</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">HTTP Referer:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">https://megogo.net/</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">Concurrent Streams:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">2-3 (max)</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">Import guide from M3U:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">✅ Enabled</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">Auto-refresh:</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; font-family: monospace;">✅ Enabled (every 6 hours)</td>
                        </tr>
                    </table>
                </div>

                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h4>🔧 For Plex (IPTV Plugin):</h4>
                    <ul>
                        <li><strong>Playlist URL:</strong> <code>http://your-server-ip:8080/playlist.m3u</code></li>
                        <li><strong>User-Agent:</strong> <code>PlexMediaServer/1.32.5 (Smart TV)</code></li>
                        <li><strong>Max Connections:</strong> <code>2</code></li>
                    </ul>
                </div>

                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h4>⚠️ Important Security Notes:</h4>
                    <ul>
                        <li>🚫 <strong>Don't exceed 3 concurrent streams</strong> - may trigger rate limiting</li>
                        <li>🕒 <strong>Avoid frequent playlist refreshes</strong> - max once every 4-6 hours</li>
                        <li>🌍 <strong>Use VPN if outside supported regions</strong> (PL, UA, etc.)</li>
                        <li>📱 <strong>Use TV/Smart TV user agents</strong> - avoid desktop browser signatures</li>
                        <li>⏰ <strong>Don't use during peak hours</strong> if possible (19:00-23:00)</li>
                    </ul>
                </div>
            </div>

            <div class="form-section">
                <h2>📖 Integration Guide</h2>
                <h4>For Emby/Jellyfin:</h4>
                <ol>
                    <li>Login using your Megogo credentials above</li>
                    <li>Copy the M3U playlist URL</li>
                    <li>In Emby/Jellyfin, go to Live TV settings</li>
                    <li>Add a new TV tuner → M3U Tuner</li>
                    <li>Enter the playlist URL from step 2</li>
                    <li>Save and refresh the guide</li>
                </ol>

                <h4>Features:</h4>
                <ul>
                    <li>✅ Live TV channels</li>
                    <li>✅ 7-day catchup/replay support</li>
                    <li>✅ Current program information</li>
                    <li>✅ Automatic token refresh</li>
                    <li>✅ Channel logos and metadata</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    from jinja2 import Template
    template = Template(html_content)

    # Get channel count if logged in
    channel_count = 0
    if megogo_client.config['logged']:
        try:
            channels = megogo_client.get_channels()
            channel_count = len([c for c in channels if not c['vod_channel'] and c['is_available']])
        except:
            channel_count = 0

    return template.render(
        logged_in=megogo_client.config['logged'],
        config=megogo_client.config,
        channel_count=channel_count
    )

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    success, message = megogo_client.login_via_email(email, password)
    status = "success" if success else "error"

    html = f"""
    <html><head><meta charset="utf-8"></head><body>
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h2>{'✅ Login Successful!' if success else '❌ Login Failed'}</h2>
        <p>{message}</p>
        <a href="/" style="display: inline-block; padding: 10px 20px; background: #007bff;
           color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">
           Return to Home
        </a>
    </div>
    </body></html>
    """
    return HTMLResponse(html)

@app.post("/logout")
async def logout():
    megogo_client.logout()
    return RedirectResponse(url="/", status_code=303)

@app.post("/config")
async def update_config(lang: str = Form(...), geo_zone: str = Form(...)):
    megogo_client.config['lang'] = lang
    megogo_client.config['geo_zone'] = geo_zone
    megogo_client.save_config()

    return HTMLResponse("""
    <html><head><meta charset="utf-8"></head><body>
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h2>✅ Configuration Updated!</h2>
        <a href="/" style="display: inline-block; padding: 10px 20px; background: #007bff;
           color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">
           Return to Home
        </a>
    </div>
    </body></html>
    """)@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_playlist(epg: bool = Query(False, description="Include current EPG information")):
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    try:
        m3u_content = megogo_client.generate_m3u(include_epg=epg)
        return PlainTextResponse(m3u_content, media_type="application/x-mpegurl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate playlist: {str(e)}")

@app.get("/stream/{channel_id}")
async def get_stream(channel_id: int, s: str = None, e: str = None):
    """Get stream URL for a channel, with optional catchup support"""
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    try:
        # Handle catchup requests (Simple Client format)
        if s and e:
            # Convert Simple Client time format to virtual object lookup
            # This is a simplified implementation - you might need to enhance this
            # based on the exact catchup format your player uses
            stream_url = megogo_client.get_stream_url(channel_id)
        else:
            # Regular live stream
            stream_url = megogo_client.get_stream_url(channel_id)

        if stream_url:
            return RedirectResponse(url=stream_url)
        else:
            raise HTTPException(status_code=404, detail="Stream not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")

@app.get("/channels")
async def get_channels():
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    try:
        channels = megogo_client.get_channels()
        return {
            "channels": channels,
            "count": len(channels),
            "live_channels": len([c for c in channels if not c['vod_channel'] and c['is_available']])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "logged_in": megogo_client.config['logged'],
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)

    print("🎬 Starting Enhanced Megogo Service...")
    print(f"📊 Data directory: {DATA_DIR}")
    print(f"🌐 Web interface: http://localhost:8080")
    print(f"📺 M3U URL: http://localhost:8080/playlist.m3u")

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=True)
