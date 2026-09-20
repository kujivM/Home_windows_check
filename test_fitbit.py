import json
import requests
import config
from datetime import datetime

TOKEN_PATH = "/home/terada/Home_windows_check/fitbit_tokens.json"

def refresh_fitbit_token(tokens):
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": config.FITBIT_CLIENT_ID,
        "client_secret": config.FITBIT_CLIENT_SECRET,
        "refresh_token": tokens.get("refresh_token"),
        "grant_type": "refresh_token"
    }
    
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        new_tokens = res.json()
        tokens.update(new_tokens)
        with open(TOKEN_PATH, "w") as f:
            json.dump(tokens, f, indent=4)
        print("🔄 [SYSTEM] トークンを自動更新しました。")
        return tokens
    else:
        print(f"❌ トークンの更新に失敗: {res.text}")
        return None

def fetch_api_data(url, tokens):
    headers = {
        "Authorization": f"Bearer {tokens.get('access_token')}",
        "Accept": "application/json"
    }
    res = requests.get(url, headers=headers, timeout=5)
    
    if res.status_code == 401:
        print(f"⚠️ 401検知: トークンをリフレッシュして再試行します...")
        tokens = refresh_fitbit_token(tokens)
        if tokens:
            headers["Authorization"] = f"Bearer {tokens.get('access_token')}"
            res = requests.get(url, headers=headers, timeout=5)
        else:
            return None, None
            
    return res.status_code, res.json() if res.status_code == 200 else res.text

def main():
    try:
        with open(TOKEN_PATH, "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ エラー: fitbit_tokens.json が見つかりません。")
        return

    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n=== DELOS UPLINK: GOOGLE HEALTH API TEST ({today_str}) ===")

    # 1. プロフィール (health.googleapis.com)
    print("\n[ FETCHING PROFILE DATA ]")
    profile_url = "https://health.googleapis.com/v4/users/me/profile"
    status, data = fetch_api_data(profile_url, tokens)
    if status == 200:
        print(f"▶ SUCCESS: 年齢 {data.get('age', '--')} 歳")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 2. 睡眠データ (health.googleapis.com)
    print("\n[ FETCHING SLEEP DATA ]")
    sleep_url = "https://health.googleapis.com/v4/users/me/dataTypes/sleep-session/dataPoints?pageSize=1"
    status, data = fetch_api_data(sleep_url, tokens)
    if status == 200:
        print(f"▶ SUCCESS (200 OK): 通信成功！")
        print(f"▶ データサンプル: {str(data.get('dataPoints', []))[:100]}...")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 3. 活動データ/歩数 (health.googleapis.com)
    print("\n[ FETCHING ACTIVITY DATA (STEPS) ]")
    activity_url = "https://health.googleapis.com/v4/users/me/dataTypes/step-count/dataPoints?pageSize=1"
    status, data = fetch_api_data(activity_url, tokens)
    if status == 200:
        print(f"▶ SUCCESS (200 OK): 通信成功！")
        print(f"▶ データサンプル: {str(data.get('dataPoints', []))[:100]}...")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 4. 心拍数データ (health.googleapis.com)
    print("\n[ FETCHING HEART RATE DATA ]")
    hr_url = "https://health.googleapis.com/v4/users/me/dataTypes/heart-rate/dataPoints?pageSize=1"
    status, data = fetch_api_data(hr_url, tokens)
    if status == 200:
        print(f"▶ SUCCESS (200 OK): 通信成功！")
        print(f"▶ データサンプル: {str(data.get('dataPoints', []))[:100]}...")
    else:
        print(f"❌ ERROR {status}: {data}")

    print("\n=== SYSTEM TEST COMPLETE ===")

if __name__ == "__main__":
    main()