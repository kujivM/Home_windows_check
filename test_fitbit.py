import json
import requests

def main():
    # 1. 保存した通行証（トークン）を読み込む
    try:
        with open("fitbit_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ エラー: fitbit_tokens.json が見つかりません。")
        return

    access_token = tokens.get("access_token")

    # 2. 通信用のヘッダー（身分証明書）をセット
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept-Language": "ja_JP"
    }

    print("\n--- FITBIT CLOUD UPLINK INITIATED ---")
    
    # 3. Fitbitサーバーからプロファイル（体重含む）を取得
    profile_url = "https://api.fitbit.com/1/user/-/profile.json"
    res = requests.get(profile_url, headers=headers)

    if res.status_code == 200:
        data = res.json().get("user", {})
        print("\n[ HOST BIOMETRICS FOUND ]")
        print(f"▶ ユーザー名: {data.get('displayName', 'Unknown')}")
        print(f"▶ 登録体重: {data.get('weight', '--')} kg")
        print(f"▶ 身長: {data.get('height', '--')} cm")
        print(f"▶ アカウント作成日: {data.get('memberSince', 'Unknown')}")
    else:
        print(f"\n❌ 通信エラー ({res.status_code}): {res.text}")
        
    print("\n-------------------------------------")

if __name__ == "__main__":
    main()