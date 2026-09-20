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
        return tokens
    return None

def fetch_api_data(url, tokens):
    headers = {
        "Authorization": f"Bearer {tokens.get('access_token')}",
        "Accept": "application/json"
    }
    res = requests.get(url, headers=headers, timeout=5)
    
    if res.status_code == 401:
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
        return

    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n=== DELOS UPLINK: FITBIT FULL METRICS TEST ({today_str}) ===")

    # 1. プロフィール
    print("\n[ FETCHING PROFILE DATA ]")
    profile_url = "https://api.fitbit.com/1/user/-/profile.json"
    status, data = fetch_api_data(profile_url, tokens)
    if status == 200:
        print(f"▶ 年齢: {data.get('user', {}).get('age', '--')} 歳")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 2. 睡眠データ
    print("\n[ FETCHING SLEEP DATA ]")
    sleep_url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{today_str}.json"
    status, data = fetch_api_data(sleep_url, tokens)
    if status == 200:
        sleep_records = data.get("sleep", [])
        if sleep_records:
            duration_hrs = round(sleep_records[0].get("duration", 0) / 3600000, 1)
            print(f"▶ 睡眠時間: {duration_hrs} 時間 (効率: {sleep_records[0].get('efficiency', 0)}%)")
        else:
            print("▶ 今日の睡眠データはまだありません。")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 3. 活動データ
    print("\n[ FETCHING ACTIVITY DATA ]")
    activity_url = f"https://api.fitbit.com/1/user/-/activities/date/{today_str}.json"
    status, data = fetch_api_data(activity_url, tokens)
    if status == 200:
        summary = data.get("summary", {})
        print(f"▶ 歩数: {summary.get('steps', 0)} 歩")
        print(f"▶ 消費カロリー: {summary.get('caloriesOut', 0)} kcal")
    else:
        print(f"❌ ERROR {status}: {data}")

    # 4. 心拍数データ
    print("\n[ FETCHING HEART RATE DATA ]")
    hr_url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{today_str}/1d.json"
    status, data = fetch_api_data(hr_url, tokens)
    if status == 200:
        hr_records = data.get("activities-heart", [])
        if hr_records:
            print(f"▶ 安静時心拍数: {hr_records[0].get('value', {}).get('restingHeartRate', '--')} BPM")
        else:
            print("▶ 心拍数データがありません。")
    else:
        print(f"❌ ERROR {status}: {data}")

if __name__ == "__main__":
    main()