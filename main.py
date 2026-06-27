import io
import re
import json
import time
import base64
import matplotlib.pyplot as plt
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google import genai
from PIL import Image

app = FastAPI()

# HTMLテンプレートの読み込み設定
templates = Jinja2Templates(directory="templates")

# ==========================================
# 設定エリア
# ==========================================
# 実績のある正しいAPIキー
API_KEY = "AQ.Ab8RN6KjH-WUprpZ82Txj35uqB7RmDtJjac5dY44HLELpJd62g"
MODEL_NAME = "gemini-2.0-flash"
# ==========================================

# Geminiクライアントの初期化
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"クライアントの初期化に失敗しました: {e}")
    client = None


def analyze_image_colors_io(img_bytes):
    """アップロードされた画像（バイトデータ）をAIに送り、色分析結果を返す"""
    if not client:
        return None, "APIクライアントが初期化されていません。APIキーを確認してください。"

    try:
        # メモリ上の画像データをPillowで開く
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        return None, f"画像の読み込みに失敗しました: {e}"

    prompt = (
        "この画像で使われている主な色を抽出し、その使用面積の割合（%）を計算してください。\n"
        "出力は必ず以下のようなJSON配列のフォーマットだけにしてください。余計な解説文や挨拶、` ```json ` のようなマークダウンの枠も一切不要です。\n"
        "[\n"
        "  {\"color\": \"#FF0000\", \"percentage\": 40},\n"
        "  {\"color\": \"#0000FF\", \"percentage\": 30}\n"
        "]"
    )

    max_retries = 3
    retry_delay = 40

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[img, prompt]
            )
            return response.text.strip(), None
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries - 1:
                    print(f"→ 429エラー検知。{retry_delay}秒待機して再試行します...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return None, "無料枠の制限（429）を超えました。約1分後に再度お試しください。"
            else:
                return None, f"APIエラーが発生しました: {e}"
    return None, "予期せぬエラーが発生しました。"


def generate_chart_base64(json_text):
    """JSONテキストから円グラフを描画し、HTML埋め込み用のBase64文字列に変換する"""
    try:
        cleaned_json = json_text
        if "```" in cleaned_json:
            cleaned_json = re.sub(r'```json|```', '', cleaned_json).strip()
        color_data = json.loads(cleaned_json)
    except Exception as e:
        return None, f"AIの出力データを解析できませんでした (JSONエラー): {e}"

    try:
        colors = [d['color'] for d in color_data]
        percentages = [d['percentage'] for d in color_data]
        labels = [f"{d['color']} ({d['percentage']}%)" for d in color_data]

        # 円グラフの描画
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(percentages, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, counterclock=False)
        ax.axis('equal')
        plt.title("Detailed Color Composition")
        plt.tight_layout()

        # グラフを保存せず、メモリ上で画像データ（PNG）に変換
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        # HTMLに直接表示できる形式（Base64文字列）にエンコード
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return img_base64, None
    except Exception as e:
        return None, f"グラフの描画中にエラーが発生しました: {e}"


# --- Webページのルーティング（画面の制御） ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """初期画面を表示する（GETリクエスト）"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, file: UploadFile = File(...)):
    """画像がアップロードされた時の処理（POSTリクエスト）"""
    if not file.filename:
        return templates.TemplateResponse("index.html", {"request": request, "error": "ファイルが選択されていません。"})

    # アップロードされた画像データを読み込む
    contents = await file.read()
    
    # 1. Geminiで色を分析
    json_result, error = analyze_image_colors_io(contents)
    if error:
        return templates.TemplateResponse("index.html", {"request": request, "error": error})

    # 2. 分析結果からグラフ（Base64）を生成
    chart_image, chart_error = generate_chart_base64(json_result)
    if chart_error:
        return templates.TemplateResponse("index.html", {"request": request, "error": chart_error})

    # 3. 結果をHTMLテンプレートに渡して画面を表示
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "chart_image": chart_image, 
            "raw_json": json_result
        }
    )


if __name__ == "__main__":
    import uvicorn
    # サーバーを起動 (http://127.0.0.1:8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)