from PIL import Image, ImageDraw, ImageFont
import subprocess
import datetime
import matplotlib.pyplot as plt
import io

def get_system_stats():
    # CPU温度の取得
    try:
        temp = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], capture_output=True, text=True)
        cpu_temp = float(temp.stdout) / 1000.0
    except:
        cpu_temp = 0.0

    # ディスク使用量の取得
    try:
        df = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        disk_usage = df.stdout.splitlines()[1].split()[4]
    except:
        disk_usage = "N/A"
        
    return f"{cpu_temp:.1f}C", disk_usage

def create_temp_graph():
    # ダミーの温度変化データ（後々はSwitchBotの履歴データ等を使います）
    times = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00']
    temps = [24.5, 25.0, 26.2, 27.5, 27.0, 26.8]

    # 白黒のグラフを作成
    plt.figure(figsize=(4, 2), dpi=100)
    plt.plot(times, temps, color='black', marker='o', linestyle='-')
    plt.title('ROOM TEMP TREND', fontsize=10, color='black')
    plt.grid(True, linestyle=':', color='gray')
    
    # 画像としてメモリに保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt.close()
    return Image.open(buf)

def generate_epaper_image():
    # M5Paperの解像度 (960 x 540) に合わせた白紙のキャンバスを作成
    width, height = 960, 540
    image = Image.new('L', (width, height), 255) # 'L'はグレースケール(白黒), 255は白
    draw = ImageDraw.Draw(image)

    # システム情報の取得
    cpu_temp, disk_usage = get_system_stats()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- 描画処理 ---
    
    # 1. 外枠とヘッダー線
    draw.rectangle((10, 10, width-10, height-10), outline=0, width=3)
    draw.line((10, 60, width-10, 60), fill=0, width=2)
    
    # 2. テキスト描画（※本来はttfフォントを読み込みますが、今回はデフォルトフォントを使用）
    draw.text((20, 20), "DELOS CORE SYSTEM - EPAPER TERMINAL", fill=0)
    draw.text((width - 200, 20), f"UPDATED: {now}", fill=0)
    
    # 3. システムステータス（文字）
    draw.text((30, 100), "[ SYSTEM DIAGNOSTICS ]", fill=0)
    draw.text((30, 140), f"CPU THERMAL: {cpu_temp}", fill=0)
    draw.text((30, 180), f"STORAGE USAGE: {disk_usage}", fill=0)
    draw.text((30, 220), f"NETWORK: ONLINE", fill=0)
    
    # 4. 環境グラフの貼り付け
    graph_img = create_temp_graph()
    # グラフを適切なサイズにリサイズして貼り付け
    graph_img = graph_img.resize((400, 200))
    image.paste(graph_img, (500, 100))

    # 画像として保存（M5Paperにはこの画像データを送ります）
    image.save('dashboard.png')
    print("電子ペーパー用画像を生成しました: dashboard.png")

if __name__ == "__main__":
    generate_epaper_image()