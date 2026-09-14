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
    "bed_hub": "8CFD4984E7F6",
    "bed_presence": "B0E9FEB96D56",
    "bed_window": "B0E9FEFF4E9E",
    "living_hub": "B0A604C54DA2",
    "living_presence": "B0E9FED6E43E",
    "living_window_front": "B0E9FEAF5149",
    "living_window_back": "B0E9FE976456"
}

def get_sb_headers():
    """SwitchBot API用の認証ヘッダーを作成"""
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = f'{config.SB_TOKEN}{t}{nonce}'
    secret_bytes = bytes(config.SB_SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')
    return {"Authorization": config.SB_TOKEN, "sign": sign, "t": str(t), "nonce": nonce, "Content-Type": "application/json; charset=utf8"}

def fetch_status(device_id):
    """個別のデバイスから最新のステータスを取得"""
    if not device_id: return None
    try:
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_sb_headers(), timeout=5)
        if res.status_code == 200: return res.json().get('body', {})
    except: pass
    return None

def get_system_stats():
    """ラズパイ本体のシステム状態を取得"""
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
    return "BREACHED (ALERT)" if win_data.get("openState") in ["open", "opened", "timeOutNotClose"] else "SECURE"

def parse_presence(pre_data):
    if not pre_data: return "OFFLINE"
    return "HOST DETECTED" if (pre_data.get('presenceState') == 'presence' or pre_data.get('moveDetected')) else "CLEAR"

def generate_epaper_image():
    width, height = 960, 540
    image = Image.new('L', (width, height), 255) # 白紙のキャンバスを作成
    draw = ImageDraw.Draw(image)

    # フォントの読み込み（ラズパイ標準フォントを使用。無ければデフォルト）
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_title = font_header = font_text = ImageFont.load_default()

    # --- 1. SwitchBot APIから本物のデータを取得 ---
    s_env = fetch_status(DEVICE_IDS["study_meter"])
    s_win = fetch_status(DEVICE_IDS["study_window"])
    b_env = fetch_status(DEVICE_IDS["bed_hub"])
    b_win = fetch_status(DEVICE_IDS["bed_window"])
    b_pre = fetch_status(DEVICE_IDS["bed_presence"])
    l_env = fetch_status(DEVICE_IDS["living_hub"])
    l_win_f = fetch_status(DEVICE_IDS["living_window_front"])
    l_pre = fetch_status(DEVICE_IDS["living_presence"])

    # --- 2. 画面の枠組みとヘッダーを描画 ---
    draw.rectangle((10, 10, width-10, height-10), outline=0, width=4)
    draw.line((10, 60, width-10, 60), fill=0, width=2)
    draw.line((480, 60, 480, height-10), fill=0, width=2) # 中央の縦線

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, 20), "DELOS CORE SYSTEM - FACILITY MONITOR", font=font_title, fill=0)
    draw.text((680, 25), f"UPDATED: {now}", font=font_text, fill=0)

    # --- 3. 左半分：FACILITY STATUS (各部屋の状況) ---
    draw.text((30, 80), "[ SECTOR 01: STUDY ]", font=font_header, fill=0)
    draw.text((50, 120), f"TEMP/HUM: {s_env.get('temperature', '--')} C / {s_env.get('humidity', '--')} %" if s_env else "TEMP/HUM: OFFLINE", font=font_text, fill=0)
    draw.text((50, 150), f"WINDOW: {parse_window(s_win)}", font=font_text, fill=0)

    draw.text((30, 210), "[ SECTOR 02: BEDROOM ]", font=font_header, fill=0)
    draw.text((50, 250), f"TEMP/HUM: {b_env.get('temperature', '--')} C / {b_env.get('humidity', '--')} %" if b_env else "TEMP/HUM: RESTRICTED", font=font_text, fill=0)
    draw.text((50, 280), f"WINDOW: {parse_window(b_win)}", font=font_text, fill=0)
    draw.text((50, 310), f"BIOMETRIC: {parse_presence(b_pre)}", font=font_text, fill=0)

    draw.text((30, 370), "[ SECTOR 03: LIVING ROOM ]", font=font_header, fill=0)
    draw.text((50, 410), f"TEMP/HUM: {l_env.get('temperature', '--')} C / {l_env.get('humidity', '--')} %" if l_env else "TEMP/HUM: RESTRICTED", font=font_text, fill=0)
    draw.text((50, 440), f"WINDOW (FRONT): {parse_window(l_win_f)}", font=font_text, fill=0)
    draw.text((50, 470), f"BIOMETRIC: {parse_presence(l_pre)}", font=font_text, fill=0)

    # --- 4. 右半分：SYSTEM DIAGNOSTICS (ラズパイ本体の状態) ---
    cpu_temp, disk_usage = get_system_stats()
    draw.text((510, 80), "[ SYSTEM DIAGNOSTICS ]", font=font_header, fill=0)
    draw.text((530, 120), f"CPU THERMAL: {cpu_temp}", font=font_text, fill=0)
    draw.text((530, 150), f"STORAGE USAGE: {disk_usage}", font=font_text, fill=0)
    draw.text((530, 180), f"NETWORK: ONLINE", font=font_text, fill=0)
    draw.text((530, 210), f"UPLINK: SWITCHBOT API V1.1", font=font_text, fill=0)

    # --- 5. LILYGO T5-4.7 PRO 用に raw bin ファイルとして書き出す ---
    raw_data = bytearray()
    pixels = image.load()
    for y in range(height):
        for x in range(0, width, 2):
            # 0〜255の明るさを4ビット（0〜15）に圧縮し、2ピクセル分を1バイトに結合
            p1 = pixels[x, y] >> 4
            p2 = pixels[x+1, y] >> 4
            raw_data.append((p1 << 4) | p2)
            
    with open('dashboard.bin', 'wb') as f:
        f.write(raw_data)
    print("本物のデータを含む電子ペーパー用画像を生成しました: dashboard.bin")

if __name__ == "__main__":
    generate_epaper_image()