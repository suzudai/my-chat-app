from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# 環境変数 GEMINI_API_KEY を設定してください
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 利用可能なモデルのリスト
AVAILABLE_MODELS = [
    "gemini-1.5-flash",
    "gemma-3-27b-it",
    "gemma-3n-e4b-it",
]

class ChatRequest(BaseModel):
    message: str
    model: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model specified.")
    
    try:
        model = genai.GenerativeModel(request.model)
        # Gemini モデルにユーザーメッセージを送信
        prompt = f"以下の内容について、マークダウン形式で詳しく説明してください。\n\n{request.message}"
        response = model.generate_content(prompt)
        # 最初のレスポンスを取り出して返却
        return ChatResponse(reply=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 静的ファイルを提供するディレクトリを作成
static_dir = "static/assets"
os.makedirs(static_dir, exist_ok=True)

# 静的ファイルをマウント
app.mount("/assets", StaticFiles(directory=static_dir), name="static")

# SPAのルーティングをサポート - すべてのパスでindex.htmlを返す
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA用のルーティング - すべてのパスでindex.htmlを返す"""
    # APIエンドポイントの場合は404を返す
    if full_path.startswith("chat"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # 静的ファイルが存在する場合はそれを返す
    static_file_path = f"static/{full_path}"
    if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
        return FileResponse(static_file_path)
    
    # それ以外はindex.htmlを返す（SPA用）
    return FileResponse("static/index.html")
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)