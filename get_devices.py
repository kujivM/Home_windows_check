import time
import hashlib
import hmac
import base64
import uuid
import requests
import json
import config

# ==========================================
# 以下の2行の ' ' の中に、先ほど取得した
# トークンとシークレットを貼り付けてください
# ==========================================
TOKEN = config.SB_TOKEN
SECRET = config.SB_SECRET

def get_device_list():
    # 1. APIと通信するための複雑な暗号署名（HMAC-SHA256）を作成
    nonce = uuid.uuid4().hex
    t = int(round(time.time() * 1000))
    string_to_sign = '{}{}{}'.format(TOKEN, t, nonce)

    secret_bytes = bytes(SECRET, 'utf-8')
    sign_term = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_bytes, sign_term, digestmod=hashlib.sha256).digest()).decode('utf-8')

    # 2. ヘッダー（通信の宛名書きのようなもの）を準備
    headers = {
        "Authorization": TOKEN,
        "sign": sign,
        "t": str(t),
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf8"
    }

    # 3. SwitchBotのサーバーへデバイス一覧を要求
    url = "https://api.switch-bot.com/v1.1/devices"
    print("SwitchBotサーバーと通信中...")
    response = requests.get(url, headers=headers)

    # 4. 結果を画面にわかりやすく表示
    if response.status_code == 200:
        devices = response.json().get('body', {}).get('deviceList', [])
        print("\n=== あなたのSwitchBotデバイス一覧 ===")
        for device in devices:
            print(f"名前: {device.get('deviceName')}")
            print(f"種類: {device.get('deviceType')}")
            print(f"デバイスID: {device.get('deviceId')}")
            print("-" * 30)
    else:
        print(f"通信エラーが発生しました: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_device_list()