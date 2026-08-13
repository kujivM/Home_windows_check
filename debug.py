import time
import hashlib
import hmac
import base64
import uuid
import requests
import config

# 設定の読み込み
SB_TOKEN = config.SB_TOKEN
SB_SECRET = config.SB_SECRET

def get_sb_headers():
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = '{}{}{}'.format(SB_TOKEN, t, nonce)
    secret_bytes = bytes(SB_SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')
    return {
        "Authorization": SB_TOKEN,
        "sign": sign,
        "t": str(t),
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf8"
    }

# 寝室のハブミニのデバイスID
TEST_DEVICE_ID = "8CFD4984E7F6"
url = f"https://api.switch-bot.com/v1.1/devices/{TEST_DEVICE_ID}/status"

print("SwitchBot APIに直接問い合わせています...")
res = requests.get(url, headers=get_sb_headers())

print("\n--- 取得結果（生データ） ---")
import json
print(json.dumps(res.json(), indent=2, ensure_ascii=False))