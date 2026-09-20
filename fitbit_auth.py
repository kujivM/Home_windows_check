import requests
import urllib.parse
import json
import config

REDIRECT_URI = 'http://127.0.0.1:8080/'

def main():
    # 1. 認証URLの生成 (最新のGoogle Health APIエンドポイント)
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    # 取得したいデータの種類（スコープ）
    SCOPES = [
    'https://www.googleapis.com/auth/fitbit.activity.read',
    'https://www.googleapis.com/auth/fitbit.heartrate.read',
    'https://www.googleapis.com/auth/fitbit.sleep.read',
    'https://www.googleapis.com/auth/fitbit.profile.read'
    ]
    
    params = {
        "client_id": config.FITBIT_CLIENT_ID,
        "response_type": "code",
        "scope": " ".join(scopes),
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline", # 自動更新のために必須
        "prompt": "consent"
    }
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*70)
    print("【STEP 1】 以下のURLをコピーして、PCのブラウザで開いてください。")
    print("="*70)
    print(url)
    print("\n※Googleアカウントでログインし、データへのアクセスをすべて「許可」してください。")
    print("※許可後、ブラウザは「このサイトにアクセスできません (127.0.0.1)」というエラー画面になりますが、それで大正解です！")
    
    print("\n" + "="*70)
    print("【STEP 2】 エラーになった画面の、ブラウザの「URL欄（アドレスバー）」を全選択してコピーし、以下に貼り付けてください。")
    print("="*70)
    
    redirected_url = input("URLを貼り付けてEnter: ").strip()
    
    # URLから「code=」の部分だけを抽出
    try:
        code_part = redirected_url.split("code=")[1]
        code = code_part.split("&")[0]
    except IndexError:
        print("\n❌ URLの形式が正しくありません。")
        print("※ブラウザのアドレスバーに「http://127.0.0.1:8080/?code=...」と表示されたURLをコピーしてください。")
        return

    # 2. アクセストークンの取得
    print("\n通信中... トークンを取得しています...")
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        "client_id": config.FITBIT_CLIENT_ID,
        "client_secret": config.FITBIT_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    res = requests.post(token_url, data=data)
    
    if res.status_code == 200:
        tokens = res.json()
        with open("fitbit_tokens.json", "w") as f:
            json.dump(tokens, f, indent=4)
        print("\n🎉 大成功！『fitbit_tokens.json』にGoogle Health APIの認証通行証を保存しました！")
    else:
        print(f"\n❌ エラーが発生しました ({res.status_code}):")
        print(res.text)

if __name__ == "__main__":
    main()