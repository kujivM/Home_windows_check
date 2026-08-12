import time
import hashlib
import hmac
import base64
import uuid
import requests
import json
import config  # <--- 追加: config.py から設定を読み込む

# ==========================================
# 以下の2行の ' ' の中に、先ほど取得した
# トークンとシークレットを貼り付けてください
# ==========================================
# 削除: TOKEN = 'ここにトークンを貼り付ける'
# 削除: SECRET = 'ここにクライアントシークレットを貼り付ける'
TOKEN = config.SB_TOKEN     # <--- 変更: config.py から読み込む
SECRET = config.SB_SECRET   # <--- 変更: config.py から読み込む

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
        body = response.json().get('body', {})
        devices = body.get('deviceList', [])
        remotes = body.get('infraredRemoteList', []) # ← ここを追加：リモコン一覧も取得

        print("\n=== あなたのSwitchBotデバイス一覧（物理機器） ===")
        for device in devices:
            print(f"名前: {device.get('deviceName')}")
            print(f"種類: {device.get('deviceType')}")
            print(f"デバイスID: {device.get('deviceId')}")
            print("-" * 30)
            
        # ↓↓↓ ここから追加：赤外線リモコンの一覧を表示する処理 ↓↓↓
        print("\n=== あなたの赤外線リモコン一覧（エアコンやテレビなど） ===")
        for remote in remotes:
            print(f"名前: {remote.get('deviceName')}")
            print(f"種類: {remote.get('remoteType')}")
            print(f"デバイスID: {remote.get('deviceId')}")
            print("-" * 30)
        # ↑↑↑ ここまで ↑↑↑

    else:
        print(f"通信エラーが発生しました: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_device_list()