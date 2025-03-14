import time
import requests
import cloudscraper
from flask import Flask, redirect, request, send_file, abort
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)

# Initialize both clients
executor = ThreadPoolExecutor(max_workers=3)  # For Tata TV
scraper = cloudscraper.create_scraper()  # For Jio TV

# Tata TV Settings
TATA_PORTAL = "tatatv.cc"
TATA_MAC = "00:1A:79:81:9A:33"
TATA_DEVICE_ID = "2D05EFECF7FE08B31042E28DDE03AF5EC85EE02E2E1A8596A905218B6E8E76EE"
TATA_DEVICE_ID2 = "2D05EFECF7FE08B31042E28DDE03AF5EC85EE02E2E1A8596A905218B6E8E76EE"
TATA_SERIAL = "C024F6E468BBD"

# Jio TV Settings
JIO_PORTAL = "jiotv.be"
JIO_MAC = "00:1A:79:1B:06:6C"
JIO_DEVICE_ID = "B7C1B08117DE65D937DE72A85D758B00BD9297F8BCAF68D674CF2127DF712F64"
JIO_DEVICE_ID2 = "B7C1B08117DE65D937DE72A85D758B00BD9297F8BCAF68D674CF2127DF712F64"
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

# Serve the Playlist File
@app.route('/playlist')
def send_playlist():
    if os.path.exists("4 tata jio 5050.m3u"):
        return send_file("4 tata jio 5050.m3u", as_attachment=False)
    else:
        abort(404, description="Playlist file not found")

# Stream Jio TV
@app.route('/jio/<channel_id>')
def jio_stream(channel_id):
    return get_stream_link(JIO_PORTAL, JIO_MAC, JIO_DEVICE_ID, JIO_DEVICE_ID2, JIO_SERIAL, JIO_SIG, channel_id)

# Stream Tata TV
@app.route('/tata/<channel_id>')
def tata_stream(channel_id):
    return get_stream_link(TATA_PORTAL, TATA_MAC, TATA_DEVICE_ID, TATA_DEVICE_ID2, TATA_SERIAL, "", channel_id)

# Fetch Streaming Link
def get_stream_link(portal, mac, device_id, device_id2, serial, sig, channel_id):
    user_ip = request.remote_addr
    timestamp = int(time.time())
    
    handshake_url = f"http://{portal}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
    headers = {
        "Cookie": f"mac={mac}; stb_lang=en; timezone=GMT",
        "X-Forwarded-For": user_ip,
        "Referer": f"http://{portal}/stalker_portal/c/",
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG250 stbapp ver: 2 rev: 250 Safari/533.3",
        "X-User-Agent": "Model: MAG250; Link:",
    }
    
    response = scraper.get(handshake_url, headers=headers, verify=False, timeout=5)
    if response.status_code != 200:
        return "Failed to retrieve authorization token", 400
    
    data = response.json()
    token = data.get("js", {}).get("random", "")
    real_token = data.get("js", {}).get("token", "")
    
    if not real_token:
        return "Failed to retrieve authorization token", 400
    
    stream_url = f"http://{portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
    headers["Authorization"] = f"Bearer {real_token}"
    response = scraper.get(stream_url, headers=headers, verify=False, timeout=5)
    
    if response.status_code == 200:
        try:
            stream_link = response.json().get("js", {}).get("cmd", "")
            if stream_link:
                return redirect(stream_link, code=302)
        except:
            return "Failed to parse stream response", 400
    return "Failed to retrieve stream link", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, threaded=True)
