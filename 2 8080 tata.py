import time
import requests
from flask import Flask, redirect, request, send_file
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=3)  # Run API calls in parallel

@app.route('/playlist')
def serve_playlist():
    return send_file(r"C:\Users\HP\Documents\m3u server\m3u\2 tata 8080.m3u", as_attachment=False)

PORTAL = "tatatv.cc"
MAC = "00:1A:79:81:9A:33"
DEVICE_ID = "2D05EFECF7FE08B31042E28DDE03AF5EC85EE02E2E1A8596A905218B6E8E76EE"
DEVICE_ID2 = "2D05EFECF7FE08B31042E28DDE03AF5EC85EE02E2E1A8596A905218B6E8E76EE"
SERIAL = "C024F6E468BBD"

def make_request(url, headers):
    """Helper function to send requests asynchronously"""
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=5)
        return response.json()
    except requests.exceptions.RequestException:
        return None

@app.route('/stream/<channel_id>')
def get_stream(channel_id):
    user_ip = request.remote_addr
    timestamp = int(time.time())
    
    # Step 1: Handshake
    url1 = f"http://{PORTAL}/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml"
    headers = {
        "Cookie": f"mac={MAC}; stb_lang=en; timezone=GMT",
        "X-Forwarded-For": user_ip,
        "Referer": f"http://{PORTAL}/stalker_portal/c/",
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG270 stbapp ver: 2 rev: 250 Safari/533.3",
        "X-User-Agent": "Model: MAG270; Link:"
    }
    
    future1 = executor.submit(make_request, url1, headers)
    data1 = future1.result()

    if not data1:
        return "Failed to retrieve authorization token", 400

    token = data1.get("js", {}).get("random", "")
    real_token = data1.get("js", {}).get("token", "")

    if not real_token:
        return "Failed to retrieve authorization token", 400

    # Step 2: Get Profile (Parallel request)
    url2 = f"http://{PORTAL}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&sn={SERIAL}&stb_type=MAG270&device_id={DEVICE_ID}&device_id2={DEVICE_ID2}&timestamp={timestamp}&metrics={{\"mac\":\"{MAC}\",\"sn\":\"{SERIAL}\",\"model\":\"MAG270\",\"type\":\"STB\",\"uid\":\"{DEVICE_ID}\",\"random\":\"{token}\"}}&JsHttpRequest=1-xml"
    headers["Authorization"] = f"Bearer {real_token}"

    executor.submit(requests.get, url2, headers)  # No need to wait for this response

    # Step 3: Generate Stream Link (Parallel request)
    url3 = f"http://{PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
    future3 = executor.submit(make_request, url3, headers)
    data3 = future3.result()

    if not data3:
        return "Failed to retrieve stream link", 400

    stream_url = data3.get("js", {}).get("cmd", "")

    if not stream_url:
        return "Failed to retrieve stream link", 400
    
    return redirect(stream_url, code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)