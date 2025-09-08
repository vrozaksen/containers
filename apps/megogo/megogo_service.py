#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import random
import hashlib
import datetime
import requests
from urllib.parse import urlencode, quote_plus
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Megogo M3U Generator", version="1.0.0")
templates = Jinja2Templates(directory="/app/templates")

# Configuration
UA = 'Dalvik/2.1.0 (Linux; U; Android 8.0.0; Unknown sdk_google_atv_x86; Build/OSR1.180418.025)'
API_URL = 'https://api.megogo.net/v1/'
DATA_DIR = '/app/data'

# API configurations (from original plugin)
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

class MegogoClient:
    def __init__(self):
        self.config_file = os.path.join(DATA_DIR, 'config.json')
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'logged': False,
            'access_token': '',
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
        except:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def generate_device_id(self):
        """Generate a device ID"""
        return 'ANDROIDTV' + self.code_gen(10, True) + '__' + self.code_gen(16)

    def code_gen(self, length, only_digit=False):
        """Generate random code"""
        base = '0123456789abcdef' if not only_digit else '0123456789'
        count = 15 if not only_digit else 9
        return ''.join(base[random.randint(0, count)] for _ in range(length))

    def get_sign(self, params):
        """Generate API signature"""
        is_drm = self.config['drm_support']
        s = ''.join([f"{k}={params[k]}" for k in params.keys()])
        s += APIS[is_drm][0]  # private_key
        s_hash = hashlib.md5(s.encode('utf-8')).hexdigest()
        s_hash += APIS[is_drm][1]  # public_key
        return s_hash

    def api_request(self, endpoint, params=None, method='GET'):
        """Make API request to Megogo"""
        if params is None:
            params = {}

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
                response = requests.get(url, headers=HEADERS, params=params)
            else:
                response = requests.post(url, headers=HEADERS, data=params)

            return response.json()
        except Exception as e:
            print(f"API request failed: {e}")
            return {'result': 'error', 'error': str(e)}

    def login_via_email(self, email, password):
        """Login using email and password"""
        params = {
            'login': email,
            'password': password,
            'remember': '1',
            'lang': self.config['lang'],
            'did': self.config['did']
        }

        headers = {**HEADERS, 'Content-Type': 'application/x-www-form-urlencoded'}
        params['sign'] = self.get_sign(params)

        response = requests.post(API_URL + 'auth/login/email', headers=headers, data=params)
        result = response.json()

        if result.get('result') == 'ok':
            user_data = result['data']['user']
            self.config.update({
                'logged': True,
                'access_token': user_data['tokens']['access_token'],
                'remember_me_token': user_data['tokens']['remember_me_token'],
                'access_key': user_data['extra']['access_key'],
                'user_id': str(user_data['user_id'])
            })
            self.save_config()
            return True, "Login successful"
        else:
            return False, result.get('error', 'Login failed')

    def get_channels(self):
        """Get list of channels"""
        result = self.api_request('tv/channels')
        if result.get('result') == 'ok':
            return result['data']['channels']
        return []

    def get_stream_url(self, channel_id):
        """Get stream URL for a channel"""
        result = self.api_request('stream', {'video_id': str(channel_id)})
        if result.get('result') == 'ok':
            stream_data = result['data']
            if 'bitrates' in stream_data and stream_data['bitrates']:
                # Get highest bitrate stream
                bitrates = sorted(stream_data['bitrates'], key=lambda x: x['bitrate'], reverse=True)
                return bitrates[0]['src']
        return None

    def generate_m3u(self):
        """Generate M3U playlist"""
        channels = self.get_channels()
        m3u_content = '#EXTM3U\n'

        for channel in channels:
            if not channel['vod_channel'] and channel['is_available']:
                name = channel['title']
                logo = channel['image']['original']
                channel_id = channel['id']

                # Create plugin URL that will be handled by our proxy
                stream_url = f"http://localhost:8080/stream/{channel_id}"

                if channel.get('is_dvr'):
                    m3u_content += f'#EXTINF:0 tvg-id="{name}" tvg-logo="{logo}" group-title="Megogo" catchup="append" catchup-source="&s={{utc:Y-m-dTH:M:S}}&e={{utcend:Y-m-dTH:M:S}}" catchup-days="7",{name}\n{stream_url}\n'
                else:
                    m3u_content += f'#EXTINF:0 tvg-id="{name}" tvg-logo="{logo}" group-title="Megogo",{name}\n{stream_url}\n'

        return m3u_content

# Initialize Megogo client
megogo_client = MegogoClient()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with configuration form"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Megogo M3U Generator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"], input[type="email"] {
                width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;
            }
            button { background-color: #007bff; color: white; padding: 10px 20px;
                     border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Megogo M3U Generator</h1>

            <div class="status info">
                <strong>Status:</strong>
                {{ "Logged in" if logged_in else "Not logged in" }}
            </div>

            {% if not logged_in %}
            <h2>Login</h2>
            <form method="post" action="/login">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
            {% endif %}

            <h2>M3U Playlist</h2>
            <p>Use this URL in your media player (Emby, Jellyfin, VLC, etc.):</p>
            <code>http://localhost:8080/playlist.m3u</code>
            <br><br>
            <a href="/playlist.m3u" target="_blank">
                <button type="button">Download M3U Playlist</button>
            </a>

            <h2>Configuration</h2>
            <form method="post" action="/config">
                <div class="form-group">
                    <label for="lang">Language:</label>
                    <input type="text" id="lang" name="lang" value="{{ config.lang }}" placeholder="pl">
                </div>
                <div class="form-group">
                    <label for="geo_zone">Geo Zone:</label>
                    <input type="text" id="geo_zone" name="geo_zone" value="{{ config.geo_zone }}" placeholder="PL">
                </div>
                <button type="submit">Save Configuration</button>
            </form>
        </div>
    </body>
    </html>
    """

    from jinja2 import Template
    template = Template(html_content)
    return template.render(
        logged_in=megogo_client.config['logged'],
        config=megogo_client.config
    )

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """Handle login"""
    success, message = megogo_client.login_via_email(email, password)
    if success:
        return HTMLResponse(f"""
        <html><body>
        <div style="text-align: center; margin-top: 50px;">
            <h2>Login Successful!</h2>
            <p>{message}</p>
            <a href="/">Return to Home</a>
        </div>
        </body></html>
        """)
    else:
        return HTMLResponse(f"""
        <html><body>
        <div style="text-align: center; margin-top: 50px;">
            <h2>Login Failed</h2>
            <p>{message}</p>
            <a href="/">Try Again</a>
        </div>
        </body></html>
        """)

@app.post("/config")
async def update_config(lang: str = Form(...), geo_zone: str = Form(...)):
    """Update configuration"""
    megogo_client.config['lang'] = lang
    megogo_client.config['geo_zone'] = geo_zone
    megogo_client.save_config()

    return HTMLResponse("""
    <html><body>
    <div style="text-align: center; margin-top: 50px;">
        <h2>Configuration Updated!</h2>
        <a href="/">Return to Home</a>
    </div>
    </body></html>
    """)

@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_playlist():
    """Generate and return M3U playlist"""
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    m3u_content = megogo_client.generate_m3u()
    return PlainTextResponse(m3u_content, media_type="application/x-mpegurl")

@app.get("/stream/{channel_id}")
async def get_stream(channel_id: int):
    """Get stream URL for a channel"""
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    stream_url = megogo_client.get_stream_url(channel_id)
    if stream_url:
        # Return redirect to actual stream
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=stream_url)
    else:
        raise HTTPException(status_code=404, detail="Stream not found")

@app.get("/channels")
async def get_channels():
    """Get list of available channels"""
    if not megogo_client.config['logged']:
        raise HTTPException(status_code=401, detail="Please login first")

    channels = megogo_client.get_channels()
    return {"channels": channels}

if __name__ == "__main__":
    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8080)
