import json
import requests

def main():
    try:
        with open("fitbit_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ エラー: fitbit_tokens.json が見つかりません。")
        return

    access_token = tokens.get("access_token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    print("\n--- GOOGLE HEALTH API UPLINK INITIATED ---")
    
    # 通信先を新しいGoogle Health APIのプロフィールエンドポイントに変更
    profile_url = "https://health.googleapis.com/v4/users/me/profile"
    res = requests.get(profile_url, headers=headers)

    if res.status_code == 200:
        data = res.json()
        print("\n[ API CONNECTION SUCCESS ]")
        print(f"▶ アカウント年齢: {data.get('age', '--')} 歳")
        date = data.get('membershipStartDate', {})
        print(f"▶ メンバー登録: {date.get('year', '----')}年{date.get('month', '--')}月")
        print("\n※現在の権限で通信テストに大成功しました！")
    else:
        print(f"\n❌ エラー ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()