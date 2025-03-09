import time
import requests
from flask import Flask, request, send_file

app = Flask(__name__)

@app.route('/playlist')
def serve_playlist():
    return send_file("ohh.m3u", as_attachment=False)

PORTAL = "tatatv.cc"
MAC = "00:1A:79:E0:19:73"
DEVICE_ID = "925655C8E5C53FEEF225FBBDBAA893FB4AC03D3472CD6FDCCF03A33660BA080D"
DEVICE_ID2 = "925655C8E5C53FEEF225FBBDBAA893FB4AC03D3472CD6FDCCF03A33660BA080D"
SERIAL = "c61fea0bd730e99badd4aafd91c025f1"
SIG = "5FFAAC99FA7EA0F56A995322D5475D565508E9FF29C2644BE84416A803D2A26C"

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
    response1 = requests.get(url1, headers=headers, verify=False)
    
    print("Handshake Response:", response1.text)  # Debugging

    if response1.status_code != 200 or not response1.text.strip():
        return f"Handshake failed: {response1.status_code} - {response1.text}", 500

    try:
        data1 = response1.json()
    except requests.exceptions.JSONDecodeError:
        return f"Handshake failed: Invalid JSON response - {response1.text}", 500

    token = data1.get("js", {}).get("random", "")
    real_token = data1.get("js", {}).get("token", "")
    
    if not real_token:
        return f"Failed to retrieve authorization token. Server response: {response1.text}", 400

    # Step 2: Get Profile
    url2 = f"http://{PORTAL}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&sn={SERIAL}&stb_type=MAG270&device_id={DEVICE_ID}&device_id2={DEVICE_ID2}&signature={SIG}&timestamp={timestamp}&metrics={{\"mac\":\"{MAC}\",\"sn\":\"{SERIAL}\",\"model\":\"MAG270\",\"type\":\"STB\",\"uid\":\"{DEVICE_ID}\",\"random\":\"{token}\"}}&JsHttpRequest=1-xml"
    headers["Authorization"] = f"Bearer {real_token}"
    response2 = requests.get(url2, headers=headers, verify=False)
    
    print("Get Profile Response:", response2.text)  # Debugging

    # Step 3: Generate Stream Link
    url3 = f"http://{PORTAL}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/{channel_id}&JsHttpRequest=1-xml"
    response3 = requests.get(url3, headers=headers, verify=False)
    
    print("Create Link Response:", response3.text)  # Debugging

    try:
        data3 = response3.json()
    except requests.exceptions.JSONDecodeError:
        return f"Create link failed: Invalid JSON response - {response3.text}", 500

    stream_url = data3.get("js", {}).get("cmd", "")

    if not stream_url:
        return f"Failed to retrieve stream link. Server response: {response3.text}", 400
    
    return f"{stream_url}", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
