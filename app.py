import time
import os
import requests
import cloudscraper
from flask import Flask, redirect, request, send_file, jsonify
from concurrent.futures import ThreadPoolExecutor

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

def make_tata_request(url, headers):
    """Helper function to send requests asynchronously for Tata TV"""
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=5)
        return response.json()
    except requests.exceptions.RequestException:
        return None
    except ValueError:  # For JSON parsing errors
        return None

def fetch_jio_token(user_ip):
    """Fetches the Bearer token and caches it for Jio TV"""
    if "token" in TOKEN_CACHE and time.time() - TOKEN_CACHE["timestamp"] < 3600:
        return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
    
    handshake_url = f"http://{JIO_PORTAL}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
    headers = JIO_BASE_HEADERS.copy()
    headers["X-Forwarded-For"] = user_ip
    headers["Cookie"] = f"mac={JIO_MAC}; stb_lang=en; timezone=GMT"
    
    try:
        response = scraper.get(handshake_url, headers=headers, verify=False, timeout=5)
        if response.status_code == 200:
            data = response.json()
            TOKEN_CACHE["random"] = data["js"].get("random")
            TOKEN_CACHE["token"] = data["js"].get("token")
            TOKEN_CACHE["timestamp"] = time.time()
            return TOKEN_CACHE["random"], TOKEN_CACHE["token"]
    except Exception as e:
        app.logger.error(f"Error fetching Jio token: {str(e)}")
    
    return None, None

# Health check route
@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Server is running"})

# Playlist Routes
@app.route('/playlist')
def playlist():
    """Serve the playlist.m3u file"""
    try:
        # First check if the file exists at the root directory
        if os.path.exists("playlist.m3u"):
            return send_file("playlist.m3u", mimetype="application/vnd.apple.mpegurl")
        else:
            return "Playlist file not found", 404
    except Exception as e:
        app.logger.error(f"Error serving playlist: {str(e)}")
        return f"Error serving playlist: {str(e)}", 500

# Jio TV Stream Route
@app.route('/jio/<channel_id>')
def jio_stream(channel_id):
    """Handle Jio TV streaming requests"""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    timestamp = int(time.time())
    
    # Step 1: Get authentication token
    token, real_token = fetch_jio_token(user_ip)
    if not real_token:
        return "Failed to retrieve authorization token", 400
    
    # Step 2: Profile request
    profile_url = f"http://{JIO_PORTAL}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&num_banks=2&sn={JIO_SERIAL}&stb_type=MAG254&device_id={JIO_DEVICE_ID}&device_id2={JIO_DEVICE_ID2}&signature={JIO_SIG}&timestamp={timestamp}&metrics={{\"mac\":\"{JIO_MAC}\",\"sn\":\"{JIO_SERIAL}\",\"model\":\"MAG254\",\"type\":\"STB\",\"uid\":\"{JIO_DEVICE_ID}\",\"random\":\"{token}\"}}&JsHttpRequest=1-xml"
    
    headers = JIO_BASE_HEADERS.copy()
    headers["X-Forwarded-For"] = user_ip
    headers["Cookie"] = f"mac={JIO_MAC}; stb_lang=en; timezone=GMT"
    headers["Authorization"] = f"Bearer {real_token}"
    
    try:
        scraper.get(profile_url, headers=headers, verify=False, timeout=5)
        
        # Step 3: Create stream link
        stream_url = f"http://{JIO_PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
        response = scraper.get(stream_url, headers=headers, verify=False, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            stream_link = data["js"].get("cmd", "")
            if stream_link:
                return redirect(stream_link, code=302)
        
        return "Failed to retrieve stream link", 400
    except Exception as e:
        app.logger.error(f"Error in Jio streaming: {str(e)}")
        return f"Error processing Jio request: {str(e)}", 500

# Tata TV Stream Route
@app.route('/tata/<channel_id>')
def tata_stream(channel_id):
    """Handle Tata TV streaming requests"""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    timestamp = int(time.time())
    
    try:
        # Step 1: Handshake
        url1 = f"http://{TATA_PORTAL}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
        headers = {
            "Cookie": f"mac={TATA_MAC}; stb_lang=en; timezone=GMT",
            "X-Forwarded-For": user_ip,
            "Referer": f"http://{TATA_PORTAL}/stalker_portal/c/",
            "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG270 stbapp ver: 2 rev: 250 Safari/533.3",
            "X-User-Agent": "Model: MAG270; Link:"
        }
        
        response1 = requests.get(url1, headers=headers, verify=False, timeout=5)
        if response1.status_code != 200:
            return "Failed to handshake with Tata TV", 400
            
        data1 = response1.json()
        token = data1.get("js", {}).get("random", "")
        real_token = data1.get("js", {}).get("token", "")
        
        if not real_token:
            return "Failed to retrieve authorization token", 400
        
        # Step 2: Get Profile
        url2 = f"http://{TATA_PORTAL}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&sn={TATA_SERIAL}&stb_type=MAG270&device_id={TATA_DEVICE_ID}&device_id2={TATA_DEVICE_ID2}&timestamp={timestamp}&metrics={{\"mac\":\"{TATA_MAC}\",\"sn\":\"{TATA_SERIAL}\",\"model\":\"MAG270\",\"type\":\"STB\",\"uid\":\"{TATA_DEVICE_ID}\",\"random\":\"{token}\"}}&JsHttpRequest=1-xml"
        headers["Authorization"] = f"Bearer {real_token}"
        
        requests.get(url2, headers=headers, verify=False, timeout=5)
        
        # Step 3: Generate Stream Link
        url3 = f"http://{TATA_PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
        response3 = requests.get(url3, headers=headers, verify=False, timeout=5)
        
        if response3.status_code != 200:
            return "Failed to generate stream link", 400
            
        data3 = response3.json()
        stream_url = data3.get("js", {}).get("cmd", "")
        
        if not stream_url:
            return "Failed to retrieve stream link", 400
            
        return redirect(stream_url, code=302)
    except Exception as e:
        app.logger.error(f"Error in Tata streaming: {str(e)}")
        return f"Error processing Tata request: {str(e)}", 500

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, threaded=True)
