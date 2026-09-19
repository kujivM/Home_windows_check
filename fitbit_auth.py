import requests
import urllib.parse
import base64
import json
import config  # config.py を読み込む

REDIRECT_URI = 'http://127.0.0.1:8080/'

def main():
    # 1. 認証URLの生成
    auth_url = "https://www.fitbit.com/oauth2/authorize"
    scope = "activity heartrate location nutrition profile settings sleep social weight"
    params = {
        "client_id": config.FITBIT_CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
        "prompt": "login consent"
    }
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*70)
    print("【STEP 1】 以下のURLをコピーして、PCのブラウザで開いてください。")
    print("="*70)
    print(url)
    print("\n※Fitbit（Google）アカウントでログインし、データへのアクセスをすべて「許可」してください。")
    print("※許可後、ブラウザは「このサイトにアクセスできません (127.0.0.1)」というエラー画面になりますが、それで大正解（正常）です！")
    
    print("\n" + "="*70)
    print("【STEP 2】 エラーになった画面の、ブラウザの「URL欄（アドレスバー）」を全選択してコピーし、以下に貼り付けてください。")
    print("="*70)
    
    redirected_url = input("URLを貼り付けてEnter: ").strip()
    
    # URLから「code=」の部分だけを抽出
    try:
        code_part = redirected_url.split("code=")[1]
        code = code_part.split("#")[0].split("&")[0]
    except IndexError:
        print("URLの形式が正しくありません。「code=...」が含まれているか確認してください。")
        return

    # 2. アクセストークンの取得
    print("\n通信中... トークンを取得しています...")
    token_url = "https://api.fitbit.com/oauth2/token"
    auth_header = base64.b64encode(f"{config.FITBIT_CLIENT_ID}:{config.FITBIT_CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": config.FITBIT_CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    res = requests.post(token_url, headers=headers, data=data)
    
    if res.status_code == 200:
        tokens = res.json()
        with open("fitbit_tokens.json", "w") as f:
            json.dump(tokens, f, indent=4)
        print("\n🎉 大成功！『fitbit_tokens.json』に認証通行証を保存しました！")
    else:
        print("\n❌ エラーが発生しました:")
        print(res.text)

if __name__ == "__main__":
    main()