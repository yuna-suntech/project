from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import ollama



app = FastAPI()

# 1. 最初にアクセスした時に表示するHTML画面を返す
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 2. 画面から文字を受け取って、Qwenに投げて、結果を返すAPI
@app.post("/chat")
async def chat_with_qwen(message: str = Form(...)):
    # Ollamaを通じてローカルのQwenを呼び出す
    response = ollama.chat(model='qwen2.5:1.5b', messages=[
        {'role': 'user', 'content': message}
    ])
    
    # AIの返答テキストだけを画面に返す
    return {"reply": response['message']['content']}




import base64
import json
import time
import requests
import os


api_key = os.environ.get("GEMINI_API_KEY")   #APIキー
MODEL_NAME = "gemini-2.5-flash"  # 画像解析用の高性能・高速モデル


# 1. 最初にアクセスした時に表示するHTML画面を返す
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

#画像を受け取る
IMAGE_PATH = "mano.png"  #イラスト

def encode_image(image_path):
    #画像を文字形式に変換する関数
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



def run_experiment():
    base64_image = encode_image(IMAGE_PATH)

    # Gemini APIのエンドポイントURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

    #プロンプト
    prompt_text = (
        "このイラストを分析し、以下の要素について、視覚的にイメージしやすい分かりやすい表現で詳細に教えてください。\n"
        "・人物の性別、髪型、服装、表情、ポーズ\n"
        "・背景（どこにいるか、何が描かれているか、どのようなモチーフが描かれているのか 等）"
    )

    # Gemini APIに送るデータ構造（ペイロード）の作成
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",  # ※JPEG画像なら image/jpeg にしてください
                            "data": base64_image,
                        }
                    },
                ]
            }
        ]
    }

    # Googleのサーバーにリクエストを送信
    response = requests.post(url, json=payload)

    # すべての処理が終わった時間を記録
    end_time = time.time()

    if response.status_code == 200:
        result = response.json()
        try:
            # Geminiから返ってきたテキスト部分を抽出
            ai_response = result["candidates"][0]["content"]["parts"][0]["text"]

            print("\n" + "=" * 50)
            print("🎯 【実験結果：Geminiによるイラスト分析（日本語）】")
            print("=" * 50)
            print(ai_response)
            print("=" * 50)

            # かかった秒数を計算
            elapsed_time = end_time - start_time
            print(f"⚡ 【実験結果：速度】全体の処理にかかった時間: {elapsed_time:.2f} 秒")
            print("=" * 50)

        except (KeyError, IndexError):
            print("❌ レスポンスの解析に失敗しました。構造が変更された可能性があります。")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Gemini APIでエラーが発生しました。ステータスコード: {response.status_code}")
        print(response.text)


