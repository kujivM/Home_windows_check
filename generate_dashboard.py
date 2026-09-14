import time
import hashlib
import hmac
import base64
import uuid
import requests
import config
import subprocess
import datetime
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# === デバイスID設定エリア ===
# ==========================================
DEVICE_IDS = {
    "study_meter": "E50F34EC2ECF",
    "study_window": "B0E9FEE6C7BA",
    "bed_presence": "B0E9FEB96D56",
    "bed_window": "B0E9FEFF4E9E",
    "living_presence": "B0E9FED6E43E",
    "living_window_front": "B0E9FEAF5149",
    "living_window_back": "B0E9FE976456"
}

def get_sb_headers():
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = f'{config.SB_TOKEN}{t}{nonce}'
    secret_bytes = bytes(config.SB_SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')
    return {"Authorization": config.SB_TOKEN, "sign": sign, "t": str(t), "nonce": nonce, "Content-Type": "application/json; charset=utf8"}

def fetch_status(device_id):
    if not device_id: return None
    try:
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_sb_headers(), timeout=5)
        if res.status_code == 200: return res.json().get('body', {})
    except: pass
    return None

def fetch_weather():
    """外気温や天気を取得（OpenWeatherMap等）"""
    try:
        # configにAPIキーや都市設定があればそれを使用、なければ横浜のデフォルト
        api_key = getattr(config, 'WEATHER_API_KEY', 'demo_key')
        lat, lon = 35.34, 139.63 # 横浜金沢区付近
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            d = res.json()
            return {
                "temp": f"{d['main']['temp']:.1f}",
                "hum": d['main']['humidity'],
                "status": d['weather'][0]['main'].upper()
            }
    except:
        pass
    return {"temp": "--", "hum": "--", "status": "OFFLINE"}

def get_system_stats():
    try:
        temp = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], capture_output=True, text=True)
        cpu_temp = f"{float(temp.stdout)/1000.0:.1f}C"
    except: cpu_temp = "N/A"
    try:
        df = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        disk = df.stdout.splitlines()[1].split()[4]
    except: disk = "N/A"
    return cpu_temp, disk

def parse_window(win_data):
    if not win_data: return "OFFLINE"
    return "BREACHED" if win_data.get("openState") in ["open", "opened", "timeOutNotClose"] else "SECURE"

def parse_presence(pre_data):
    if not pre_data: return "OFFLINE"
    return "HOST DETECTED" if (pre_data.get('presenceState') == 'presence' or pre_data.get('moveDetected')) else "CLEAR"

def generate_epaper_image():
    width, height = 960, 540
    image = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_title = font_header = font_text = ImageFont.load_default()

    # --- データの取得 ---
    s_env = fetch_status(DEVICE_IDS["study_meter"])
    s_win = fetch_status(DEVICE_IDS["study_window"])
    b_win = fetch_status(DEVICE_IDS["bed_window"])
    b_pre = fetch_status(DEVICE_IDS["bed_presence"])
    l_win_f = fetch_status(DEVICE_IDS["living_window_front"])
    l_pre = fetch_status(DEVICE_IDS["living_presence"])
    weather = fetch_weather()
    cpu_temp, disk_usage = get_system_stats()

    # --- 画面の枠組み描画 ---
    draw.rectangle((10, 10, width-10, height-10), outline=0, width=3)
    draw.line((10, 55, width-10, 55), fill=0, width=2)     # メインヘッダー下の線
    draw.line((10, 95, width-10, 95), fill=0, width=2)     # 外気バー下の線
    draw.line((480, 95, 480, height-10), fill=0, width=2)  # 左右分割の縦線

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, 18), "DELOS CORE SYSTEM - FACILITY MONITOR", font=font_title, fill=0)
    draw.text((650, 22), f"UPDATED: {now}", font=font_text, fill=0)

    # --- 外界テレメトリーバー (EXTERNAL TELEMETRY) ---
    draw.text((20, 64), f"▶ EXTERNAL [YOKOHAMA]: {weather['status']} / TEMP: {weather['temp']}C / HUM: {weather['hum']}%", font=font_header, fill=0)

    # --- 左半分：FACILITY STATUS (各部屋の状況) ---
    draw.text((30, 110), "[ SECTOR 01: STUDY ]", font=font_header, fill=0)
    draw.text((50, 145), f"TEMP/HUM: {s_env.get('temperature', '--')} C / {s_env.get('humidity', '--')} %" if s_env else "TEMP/HUM: OFFLINE", font=font_text, fill=0)
    draw.text((50, 175), f"WINDOW: {parse_window(s_win)}", font=font_text, fill=0)

    draw.text((30, 230), "[ SECTOR 02: BEDROOM ]", font=font_header, fill=0)
    draw.text((50, 265), f"TEMP/HUM: NO SIGNAL (RESTRICTED)", font=font_text, fill=0)
    draw.text((50, 295), f"WINDOW: {parse_window(b_win)}", font=font_text, fill=0)
    draw.text((50, 325), f"BIOMETRIC: {parse_presence(b_pre)}", font=font_text, fill=0)

    draw.text((30, 380), "[ SECTOR 03: LIVING ROOM ]", font=font_header, fill=0)
    draw.text((50, 415), f"TEMP/HUM: NO SIGNAL (RESTRICTED)", font=font_text, fill=0)
    draw.text((50, 445), f"WINDOW (FRONT): {parse_window(l_win_f)}", font=font_text, fill=0)
    draw.text((50, 475), f"BIOMETRIC: {parse_presence(l_pre)}", font=font_text, fill=0)

    # --- 右半分：SYSTEM DIAGNOSTICS (ラズパイ本体の状態) ---
    draw.text((510, 110), "[ SYSTEM DIAGNOSTICS ]", font=font_header, fill=0)
    draw.text((530, 150), f"CPU THERMAL: {cpu_temp}", font=font_text, fill=0)
    draw.text((530, 190), f"STORAGE USAGE: {disk_usage}", font=font_text, fill=0)
    draw.text((530, 230), f"NETWORK: ONLINE", font=font_text, fill=0)
    draw.text((530, 270), f"UPLINK: SWITCHBOT API V1.1", font=font_text, fill=0)
    draw.text((530, 310), f"HARDWARE: LILYGO T5-4.7 PRO", font=font_text, fill=0)

    # --- binファイルとして保存 ---
    raw_data = bytearray()
    pixels = image.load()
    for y in range(height):
        for x in range(0, width, 2):
            p1 = pixels[x, y] >> 4
            p2 = pixels[x+1, y] >> 4
            raw_data.append((p1 << 4) | p2)
            
    with open('dashboard.bin', 'wb') as f:
        f.write(raw_data)
    print("外気温を含む最新の電子ペーパー用画像を生成しました: dashboard.bin")

if __name__ == "__main__":
    generate_epaper_image()