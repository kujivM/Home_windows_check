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
TARGET_WINDOWS = {
    'B0E9FE976456': '食堂側窓',
    'B0E9FEAF5149': '居間側窓',
    'B0E9FEE6C7BA': '書斎側窓',
    'B0E9FEFF4E9E': '寝室窓'
}

# 4. 各部屋の「存在センサー」と「エアコン」のデバイスID
TARGET_ROOMS = {
    '寝室': {
        'sensor_id': 'B0E9FEB96D56',
        'ac_id': '01-202608111138-03240109'
    },
    '居間': {
        'sensor_id': 'B0E9FED6E43E',
        'ac_id': '01-202608111119-90959291'
    }
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

def check_presence(headers, sensor_id):
    """存在センサーの状態を確認する関数"""
    url = f"https://api.switch-bot.com/v1.1/devices/{sensor_id}/status"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            body = data.get('body', {})
            # 人がいる(presence) または 動体検知(True) の場合は人がいると判定
            if body.get('presenceState') == 'presence' or body.get('moveDetected') == True:
                return True
            else:
                return False
    except Exception as e:
        print(f"センサーの通信エラーが発生しました: {e}")
    
    # エラー時は安全のため「人がいる」と仮定して、誤ってエアコンを消すのを防ぐ
    return True

def turn_off_ac(headers, ac_id):
    """エアコンをOFFにする関数"""
    url = f"https://api.switch-bot.com/v1.1/devices/{ac_id}/commands"
    data = {
        "commandType": "command",
        "command": "turnOff",
        "parameter": "default"
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"エアコンOFF送信エラー: {e}")
    return False

def main():
    headers = get_sb_headers()
    open_windows = []

    # 1. 窓の開閉チェック
    print("窓の状態をチェックしています...")
    for device_id, window_name in TARGET_WINDOWS.items():
        url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/status"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                open_state = data.get('body', {}).get('openState')
                print(f"{window_name}: {open_state}")
                if open_state == "open" or open_state == "timeOutNotClose":
                    open_windows.append(window_name)
            else:
                print(f"[{window_name}] の状態取得に失敗しました: {response.status_code}")
        except Exception as e:
            print(f"[{window_name}] 通信エラーが発生しました: {e}")
        
        # API制限対策
        time.sleep(1)

    # 2. 各部屋の人の有無をチェックしてエアコンを操作
    print("各部屋の人の有無をチェックしています...")
    ac_messages = []
    for room_name, devices in TARGET_ROOMS.items():
        sensor_id = devices['sensor_id']
        ac_id = devices['ac_id']
        
        if 'ここに' in sensor_id or 'ここに' in ac_id:
            continue
            
        is_someone_present = check_presence(headers, sensor_id)
        
        if is_someone_present:
            ac_messages.append(f"👤 {room_name}: 人がいるため、エアコンはそのままにしました。")
        else:
            if turn_off_ac(headers, ac_id):
                ac_messages.append(f"❄️ {room_name}: 誰もいないため、エアコンを自動でOFFにしました。")
            else:
                ac_messages.append(f"❌ {room_name}: エアコンのOFF操作に失敗しました。")
        
        time.sleep(1)

    # 3. LINEメッセージの組み立て
    message_lines = []

    # 窓のメッセージ
    if len(open_windows) > 0:
        windows_str = "、".join(open_windows)
        message_lines.append(f"\u26A0\uFE0F {windows_str} が開いています！確認してください。")
    else:
        message_lines.append("\u2705 すべての窓が閉まっています。戸締まりOK！")

    # エアコンのメッセージを追加
    if len(ac_messages) > 0:
        message_lines.append("") # 1行空ける
        for msg in ac_messages:
            message_lines.append(msg)
    
    # メッセージを結合して送信
    message = "\n".join(message_lines)
    print("\n--- 判定結果 ---")
    print(message)
    send_line_message(message)

if __name__ == "__main__":
    main()