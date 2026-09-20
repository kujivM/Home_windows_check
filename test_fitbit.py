import json
import requests
import config  # config.py からクライアント情報を読み込む

def refresh_fitbit_token(tokens):
    """リフレッシュトークンを使って新しい鍵を取得する関数"""
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": config.FITBIT_CLIENT_ID,         # config.pyの変数名に合わせてください
        "client_secret": config.FITBIT_CLIENT_SECRET, # config.pyの変数名に合わせてください
        "refresh_token": tokens.get("refresh_token"),
        "grant_type": "refresh_token"
    }
    
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        new_tokens = res.json()
        # 新しい鍵情報を上書き
        tokens.update(new_tokens)
        # JSONファイルに保存し直す
        with open("/home/terada/Home_windows_check/fitbit_tokens.json", "w") as f:
            json.dump(tokens, f, indent=4)
        print("🔄 [SYSTEM] アクセストークンの自動更新に成功しました！")
        return tokens
    else:
        print(f"❌ トークンの更新に失敗しました: {res.text}")
        return None

def main():
    try:
        with open("/home/terada/Home_windows_check/fitbit_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ エラー: fitbit_tokens.json が見つかりません。")
        return

    print("\n--- GOOGLE HEALTH API UPLINK INITIATED ---")
    
    access_token = tokens.get("access_token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    profile_url = "https://health.googleapis.com/v4/users/me/profile"
    
    # 1回目の通信
    res = requests.get(profile_url, headers=headers)

    # もし401（期限切れ）エラーが返ってきたら、リフレッシュ処理を発動
    if res.status_code == 401:
        print("⚠️ 鍵の有効期限切れ(401)を検知。リフレッシュ・シーケンスを実行します...")
        tokens = refresh_fitbit_token(tokens)
        if tokens:
            # 新しい鍵でヘッダーを作り直して再チャレンジ
            headers["Authorization"] = f"Bearer {tokens.get('access_token')}"
            res = requests.get(profile_url, headers=headers)
        else:
            return

    # 最終的な結果の処理
    if res.status_code == 200:
        data = res.json()
        print("\n[ API CONNECTION SUCCESS ]")
        print(f"▶ アカウント年齢: {data.get('age', '--')} 歳")
        date = data.get('membershipStartDate', {})
        print(f"▶ メンバー登録: {date.get('year', '----')}年{date.get('month', '--')}月")
    else:
        print(f"\n❌ エラー ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()