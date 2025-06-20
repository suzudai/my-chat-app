from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import google.generativeai as genai
import uvicorn
from dotenv import load_dotenv

# このファイルのディレクトリを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# １つ上の階層のディレクトリ（プロジェクトルート）を取得
project_root = os.path.dirname(current_dir)
# 静的ファイルディレクトリのパスを作成
static_file_dir = os.path.join(project_root, "backend/static")

# routersからchatルーターをインポート
from routers import chat
from routers import new_api
from routers import chat_langchain
from routers import chat_langchain_rag
load_dotenv()

app = FastAPI()

# 環境変数 GEMINI_API_KEY を設定
# この設定はアプリケーションの起動時に一度だけ行われるべきです。
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # APIキーがない場合はエラーメッセージを出力するか、アプリケーションを終了するのが望ましい
    print("警告: 環境変数 'GEMINI_API_KEY' が設定されていません。")
else:
    genai.configure(api_key=api_key)

# APIルーターをインクルードします。 '/api' というプレフィックスが付きます。
# これにより、このルーター内のすべてのパスは '/api' から始まります (例: /api/chat)
app.include_router(chat.router, prefix="/api")
app.include_router(new_api.router, prefix="/api/new")
app.include_router(chat_langchain.router, prefix="/api/langchain")
app.include_router(chat_langchain_rag.router, prefix="/api/langchainchatrag")

# Viteによってビルドされた静的ファイルを配信します。
app.mount("/assets", StaticFiles(directory=os.path.join(static_file_dir, "assets")), name="assets")

# SPA (Single Page Application) のためのキャッチオールルート
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    フロントエンドアプリケーションをホストするためのフォールバック。
    """
    return FileResponse(os.path.join(static_file_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)