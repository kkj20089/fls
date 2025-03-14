import time
import cloudscraper
from flask import Flask, request, redirect, send_file

app = Flask(__name__)

# IPTV Settings
PORTAL = "jiotv.be"
MAC = "00:1A:79:1B:06:6C"
DEVICE_ID = "B7C1B08117DE65D937DE72A85D758B00BD9297F8BCAF68D674CF2127DF712F64"
DEVICE_ID2 = "B7C1B08117DE65D937DE72A85D758B00BD9297F8BCAF68D674CF2127DF712F64"
SERIAL = "4A3361CFC51F8"
SIG = ""  # Not available

# Use CloudScraper to bypass Cloudflare
scraper = cloudscraper.create_scraper()

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
    "X-User-Agent": "Model: MAG250; Link:",
    "Referer": f"http://{PORTAL}/stalker_portal/c/",
}

TOKEN_CACHE = {}

def fetch_token(user_ip):
    """Fetches the Bearer token and caches it to avoid rate limits."""
    if "token" in TOKEN_CACHE and time.time() - TOKEN_CACHE["timestamp"] < 3600:
        return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
    
    handshake_url = f"http://{PORTAL}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
    headers = BASE_HEADERS.copy()
    headers["X-Forwarded-For"] = user_ip
    headers["Cookie"] = f"mac={MAC}; stb_lang=en; timezone=GMT"
    
    response = scraper.get(handshake_url, headers=headers, verify=False, timeout=5)
    if response.status_code == 200:
        try:
            data = response.json()
            TOKEN_CACHE["random"] = data["js"].get("random")
            TOKEN_CACHE["token"] = data["js"].get("token")
            TOKEN_CACHE["timestamp"] = time.time()
            return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
        except:
            return None, None
    return None, None

@app.route('/stream/<channel_id>')
def get_stream(channel_id):
    user_ip = request.remote_addr
    timestamp = int(time.time())
    
    token, real_token = fetch_token(user_ip)
    if not real_token:
        return "Failed to retrieve authorization token", 400
    
    profile_url = f"http://{PORTAL}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&num_banks=2&sn={SERIAL}&stb_type=MAG254&device_id={DEVICE_ID}&device_id2={DEVICE_ID2}&signature={SIG}&timestamp={timestamp}&metrics={{\"mac\":\"{MAC}\",\"sn\":\"{SERIAL}\",\"model\":\"MAG254\",\"type\":\"STB\",\"uid\":\"{DEVICE_ID}\",\"random\":\"{token}\"}}&JsHttpRequest=1-xml"
    headers = BASE_HEADERS.copy()
    headers["X-Forwarded-For"] = user_ip
    headers["Cookie"] = f"mac={MAC}; stb_lang=en; timezone=GMT"
    headers["Authorization"] = f"Bearer {real_token}"
    
    scraper.get(profile_url, headers=headers, verify=False, timeout=5)
    
    stream_url = f"http://{PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
    response = scraper.get(stream_url, headers=headers, verify=False, timeout=5)
    
    if response.status_code == 200:
        try:
            data = response.json()
            stream_link = data["js"].get("cmd", "")
            if stream_link:
                return redirect(stream_link, code=302)  # ✅ Correct redirect status code
        except:
            return "Failed to parse stream response", 400
    return "Failed to retrieve stream link", 400

# ✅ Added Playlist Route
@app.route('/playlist')
def serve_playlist():
    m3u_file_path = r"C:\Users\HP\Documents\m3u server\m3u\3 jio 5050.m3u"
    return send_file(m3u_file_path, as_attachment=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, threaded=True)
