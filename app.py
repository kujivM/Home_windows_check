from flask import Flask, render_template, jsonify
import time
import hashlib
import hmac
import base64
import uuid
import requests
import subprocess
import shutil
import config

app = Flask(__name__)

# ==========================================
# === デバイスID設定エリア ===
# ==========================================
DEVICE_IDS = {
    "study_meter": "E50F34EC2ECF", "study_window": "B0E9FEE6C7BA", "study_light": "C1AE772DEF7B", 
    "bed_window": "B0E9FEFF4E9E", "bed_presence": "B0E9FEB96D56", 
    "living_window_front": "B0E9FEAF5149", "living_window_back": "B0E9FE976456",
    "living_presence": "B0E9FED6E43E", "dining_light": "E89B99AC78FB", "living_light": "FAD5E7882CD9"
}
# ==========================================

def get_sb_headers():
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = '{}{}{}'.format(config.SB_TOKEN, t, nonce)
    secret_bytes = bytes(config.SB_SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')
    return {"Authorization": config.SB_TOKEN, "sign": sign, "t": str(t), "nonce": nonce, "Content-Type": "application/json; charset=utf8"}

def fetch_device_status(device_id):
    if not device_id: return None
    try:
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_sb_headers(), timeout=5)
        if res.status_code == 200: return res.json().get('body', {})
    except: pass
    return None

# --- ★メイン画面（1ページ目） ---
@app.route('/')
def index():
    return render_template('westworld.html')

# --- ★端末診断画面（2ページ目）の追加 ---
@app.route('/system')
def system_page():
    return render_template('westworld_system.html')

# --- ★アプリ認定用マニフェスト ---
@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "DELOS SYSTEM MATRIX", "short_name": "DELOS", "start_url": "/", "display": "fullscreen",
        "background_color": "#090e11", "theme_color": "#090e11",
        "icons": [
            {"src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgZmlsbD0iIzA5MGUxMSIvPjx0ZXh0IHg9Ijk2IiB5PSI5NiIgZmlsbD0iIzRkZjhmZiIgZm9udC1zaXplPSIzMCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPkRFTE9TPC90ZXh0Pjwvc3ZnPg==", "sizes": "192x192", "type": "image/svg+xml"}
        ]
    })

# --- ★システム情報取得API（2ページ目用） ---
@app.route('/api/system_status')
def get_system_status():
    # ディスク容量取得
    try:
        disk = shutil.disk_usage('/data/data/com.termux/files/home')
        disk_total = round(disk.total / (1024 ** 3), 1)
        disk_used = round((disk.total - disk.free) / (1024 ** 3), 1)
        disk_percent = round(((disk.total - disk.free) / disk.total) * 100, 1)
    except:
        disk_total, disk_used, disk_percent = 0, 0, 0

    # topコマンドの実行（上位20行だけ取得してターミナル感を出す）
    try:
        top_raw = subprocess.check_output(['top', '-n', '1'], text=True, timeout=3)
        top_text = "\n".join(top_raw.split("\n")[:20])
    except Exception as e:
        top_text = f"TERMINAL UPLINK ERROR:\n{e}"

    return jsonify({"disk_total": disk_total, "disk_used": disk_used, "disk_percent": disk_percent, "top_text": top_text})

# --- メイン画面用API ---
@app.route('/api/status')
def get_status():
    # （※前回のコードと同じ内容です）
    response_data = {
        "study": {"temp": "--", "hum": "--", "window": "UNKNOWN", "light": "OFFLINE"},
        "bed": {"temp": "RESTRICTED", "hum": "RESTRICTED", "window": "UNKNOWN", "presence": False},
        "living": {"temp": "RESTRICTED", "hum": "RESTRICTED", "window_front": "UNKNOWN", "window_back": "UNKNOWN", "presence": False, "dining_light": "OFFLINE", "living_light": "OFFLINE"}
    }
    s_env = fetch_device_status(DEVICE_IDS["study_meter"])
    if s_env:
        response_data["study"]["temp"] = s_env.get("temperature", "--")
        response_data["study"]["hum"] = s_env.get("humidity", "--")
    s_win = fetch_device_status(DEVICE_IDS["study_window"])
    if s_win: response_data["study"]["window"] = s_win.get("openState", "UNKNOWN")
    s_lgt = fetch_device_status(DEVICE_IDS["study_light"])
    if s_lgt: response_data["study"]["light"] = s_lgt.get("power", "ON")

    b_win = fetch_device_status(DEVICE_IDS["bed_window"])
    if b_win: response_data["bed"]["window"] = b_win.get("openState", "UNKNOWN")
    b_pre = fetch_device_status(DEVICE_IDS["bed_presence"])
    if b_pre: response_data["bed"]["presence"] = (b_pre.get('presenceState') == 'presence' or b_pre.get('moveDetected') == True)

    l_win_f = fetch_device_status(DEVICE_IDS["living_window_front"])
    if l_win_f: response_data["living"]["window_front"] = l_win_f.get("openState", "UNKNOWN")
    l_win_b = fetch_device_status(DEVICE_IDS["living_window_back"])
    if l_win_b: response_data["living"]["window_back"] = l_win_b.get("openState", "UNKNOWN")
    l_pre = fetch_device_status(DEVICE_IDS["living_presence"])
    if l_pre: response_data["living"]["presence"] = (l_pre.get('presenceState') == 'presence' or l_pre.get('moveDetected') == True)
        
    d_lgt = fetch_device_status(DEVICE_IDS["dining_light"])
    if d_lgt: response_data["living"]["dining_light"] = d_lgt.get("power", "ON")
    l_lgt = fetch_device_status(DEVICE_IDS["living_light"])
    if l_lgt: response_data["living"]["living_light"] = l_lgt.get("power", "ON")

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)