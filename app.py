import os
import time
import requests
import cloudscraper
from flask import Flask, redirect, request, send_file, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Initialize clients
executor = ThreadPoolExecutor(max_workers=3)  # For Tata TV
scraper = cloudscraper.create_scraper()  # For Jio TV

# Tata TV Settings
TATA_PORTAL = "tatatv.cc"
TATA_MAC = "00:1A:79:81:9A:33"
TATA_DEVICE_ID = "2D05EFECF7FE08B31042E28DDE03AF5EC85EE02E2E1A8596A905218B6E8E76EE"
TATA_SERIAL = "C024F6E468BBD"

# Jio TV Settings
JIO_PORTAL = "jiotv.be"
JIO_MAC = "00:1A:79:1B:06:6C"
JIO_DEVICE_ID = "B7C1B08117DE65D937DE72A85D758B00BD9297F8BCAF68D674CF2127DF712F64"
JIO_SERIAL = "4A3361CFC51F8"
JIO_SIG = ""

# Base headers for Jio TV
JIO_BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
    "X-User-Agent": "Model: MAG250; Link:",
    "Referer": f"http://{JIO_PORTAL}/stalker_portal/c/",
}

# Token cache for Jio TV
TOKEN_CACHE = {}

def fetch_jio_token(user_ip):
    """Fetches the Bearer token and caches it for Jio TV, with logging for debugging"""
    if "token" in TOKEN_CACHE and time.time() - TOKEN_CACHE["timestamp"] < 3600:
        return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
    
    handshake_url = f"http://{JIO_PORTAL}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
    headers = JIO_BASE_HEADERS.copy()
    headers["X-Forwarded-For"] = user_ip
    headers["Cookie"] = f"mac={JIO_MAC}; stb_lang=en; timezone=GMT"
    
    try:
        response = scraper.get(handshake_url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        TOKEN_CACHE["random"] = data["js"].get("random")
        TOKEN_CACHE["token"] = data["js"].get("token")
        TOKEN_CACHE["timestamp"] = time.time()
        app.logger.info(f"Jio Token Fetched: {TOKEN_CACHE}")
        return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
    except Exception as e:
        app.logger.error(f"Error fetching Jio token: {str(e)} - Response: {response.text if response else 'No Response'}")
        return None, None

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/playlist')
def serve_playlist():
    """Serve the playlist file from the current directory"""
    if os.path.exists("playlist.m3u"):
        return send_file("playlist.m3u", mimetype="application/vnd.apple.mpegurl")
    return "Playlist file not found", 404

@app.route('/jio/<channel_id>')
def jio_stream(channel_id):
    """Handle Jio TV streaming requests"""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    token, real_token = fetch_jio_token(user_ip)
    if not real_token:
        return "Failed to retrieve authorization token", 400
    
    stream_url = f"http://{JIO_PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
    try:
        response = scraper.get(stream_url, headers=JIO_BASE_HEADERS, timeout=5)
        response.raise_for_status()
        data = response.json()
        stream_link = data["js"].get("cmd", "")
        if stream_link:
            return redirect(stream_link, code=302)
    except Exception as e:
        app.logger.error(f"Error fetching Jio stream: {str(e)} - Response: {response.text if response else 'No Response'}")
        return "Failed to retrieve stream link", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, threaded=True)
