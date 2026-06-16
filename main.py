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