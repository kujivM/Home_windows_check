import time
import hashlib
import hmac
import base64
import uuid
import requests
import config

# ==========================================
# === 設定エリア ===
# ==========================================

# 1. SwitchBotのAPIキー
SB_TOKEN = config.SB_TOKEN
SB_SECRET = config.SB_SECRET

# 2. LINE APIのキー（MacroDroidに設定したものと同じ）
LINE_ACCESS_TOKEN = config.LINE_ACCESS_TOKEN
LINE_USER_ID = config.LINE_USER_ID

# 3. 監視したい開閉センサーの「デバイスID」と「窓の名前」
# 先ほど取得したデバイスIDを左側に、分かりやすい名前を右側に書きます
TARGET_WINDOWS = {
    'B0E9FE976456': '食堂側窓',
    'B0E9FEAF5149': '居間側窓',
    'B0E9FEE6C7BA': '書斎側窓',
    'B0E9FEFF4E9E': '寝室窓'
}

# ==========================================

def get_sb_headers():
    """SwitchBot API用の認証ヘッダーを作成する関数"""
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

def send_line_message(text):
    """LINEにメッセージを送信する関数"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("LINEへ通知を送信しました。")
    else:
        print(f"LINE通知エラー: {response.status_code}\n{response.text}")

def main():
    print("窓の状態をチェックしています...")
    headers = get_sb_headers()

    open_windows = [] # 開いている窓の名前を入れるリスト

    # 設定した4つのデバイスを順番にチェック
    for device_id, window_name in TARGET_WINDOWS.items():
        url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/status"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # センサーの状態（open か close）を取得
                open_state = data.get('body', {}).get('openState')

                print(f"{window_name}: {open_state}")

                if open_state == "open" or open_state == "timeOutNotClose":
                    open_windows.append(window_name)
            else:
                print(f"[{window_name}] の状態取得に失敗しました: {response.status_code}")

        except Exception as e:
            print(f"[{window_name}] 通信エラーが発生しました: {e}")

        # APIの制限に引っかからないよう、1秒待機
        time.sleep(1)

    # チェック結果からLINEのメッセージを作成して送信
    if len(open_windows) > 0:
        # 開いている窓がある場合
        windows_str = "、".join(open_windows)
        message = f"\u26A0\uFE0F {windows_str} が開いています！確認してください。"
    else:
        # すべて閉まっている場合
        message = "\u2705 すべての窓が閉まっています。戸締まりOK！"

    print("\n--- 判定結果 ---")
    print(message)

    # LINEに送信
    send_line_message(message)

if __name__ == "__main__":
    main()