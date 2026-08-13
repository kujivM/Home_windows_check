from flask import Flask, render_template, jsonify
import time
import hashlib
import hmac
import base64
import uuid
import requests
import config

app = Flask(__name__)

# ==========================================
# === デバイスID設定エリア ===
# ==========================================
DEVICE_IDS = {
    # --- 書斎 (SECTOR 01) ---
    "study_meter": "E50F34EC2ECF",
    "study_window": "B0E9FEE6C7BA",
    "study_light": "C1AE772DEF7B", 

    # --- 寝室 (SECTOR 02) ---
    "bed_window": "B0E9FEFF4E9E",
    "bed_presence": "B0E9FEB96D56", 

    # --- 居間 (SECTOR 03) ---
    "living_window_front": "B0E9FEAF5149",
    "living_window_back": "B0E9FE976456",
    "living_presence": "B0E9FED6E43E",
    "dining_light": "E89B99AC78FB",
    "living_light": "FAD5E7882CD9"
}
# ==========================================

def get_sb_headers():
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = '{}{}{}'.format(config.SB_TOKEN, t, nonce)
    secret_bytes = bytes(config.SB_SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')
    return {
        "Authorization": config.SB_TOKEN,
        "sign": sign,
        "t": str(t),
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf8"
    }

def fetch_device_status(device_id):
    if not device_id:
        return None
    url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/status"
    try:
        res = requests.get(url, headers=get_sb_headers(), timeout=5)
        if res.status_code == 200:
            return res.json().get('body', {})
    except Exception as e:
        print(f"API Error ({device_id}): {e}")
    return None

@app.route('/')
def index():
    return render_template('westworld.html')

@app.route('/api/status')
def get_status():
    response_data = {
        "study": {"temp": "--", "hum": "--", "window": "UNKNOWN", "light": "OFFLINE"},
        "bed": {"temp": "RESTRICTED", "hum": "RESTRICTED", "window": "UNKNOWN", "presence": False},
        "living": {
            "temp": "RESTRICTED", "hum": "RESTRICTED", 
            "window_front": "UNKNOWN", "window_back": "UNKNOWN", 
            "presence": False,
            "dining_light": "OFFLINE", "living_light": "OFFLINE"
        }
    }

    # 書斎 (ここは本物の温湿度が取れます)
    s_env = fetch_device_status(DEVICE_IDS["study_meter"])
    if s_env:
        response_data["study"]["temp"] = s_env.get("temperature", "--")
        response_data["study"]["hum"] = s_env.get("humidity", "--")
    s_win = fetch_device_status(DEVICE_IDS["study_window"])
    if s_win:
        response_data["study"]["window"] = s_win.get("openState", "UNKNOWN")
    s_lgt = fetch_device_status(DEVICE_IDS["study_light"])
    if s_lgt:
        response_data["study"]["light"] = s_lgt.get("power", "ON")

    # 寝室
    b_win = fetch_device_status(DEVICE_IDS["bed_window"])
    if b_win:
        response_data["bed"]["window"] = b_win.get("openState", "UNKNOWN")
    b_pre = fetch_device_status(DEVICE_IDS["bed_presence"])
    if b_pre:
        response_data["bed"]["presence"] = (b_pre.get('presenceState') == 'presence' or b_pre.get('moveDetected') == True)

    # 居間
    l_win_f = fetch_device_status(DEVICE_IDS["living_window_front"])
    if l_win_f:
        response_data["living"]["window_front"] = l_win_f.get("openState", "UNKNOWN")
    l_win_b = fetch_device_status(DEVICE_IDS["living_window_back"])
    if l_win_b:
        response_data["living"]["window_back"] = l_win_b.get("openState", "UNKNOWN")
    l_pre = fetch_device_status(DEVICE_IDS["living_presence"])
    if l_pre:
        response_data["living"]["presence"] = (l_pre.get('presenceState') == 'presence' or l_pre.get('moveDetected') == True)
        
    d_lgt = fetch_device_status(DEVICE_IDS["dining_light"])
    if d_lgt:
        response_data["living"]["dining_light"] = d_lgt.get("power", "ON")
    l_lgt = fetch_device_status(DEVICE_IDS["living_light"])
    if l_lgt:
        response_data["living"]["living_light"] = l_lgt.get("power", "ON")

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)