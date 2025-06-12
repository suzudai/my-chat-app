from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import google.generativeai as genai
import uvicorn
from dotenv import load_dotenv

# routersからchatルーターをインポート
from routers import chat
from routers import new_api

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

# Viteによってビルドされた静的ファイルを配信します。
# 'static' ディレクトリを '/assets' パスにマウントします。
# Viteのビルド設定(vite.config.ts)で 'assetsDir' を変更していない場合、
# JavaScriptやCSSファイルは 'assets' ディレクトリ内に生成されます。
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

# SPA (Single Page Application) のためのキャッチオールルート
# APIでも静的ファイルでもない他のすべてのパスリクエストに対して
# フロントエンドのメインのHTMLファイル (index.html) を返します。
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Vue/Reactなどのフロントエンドアプリケーションをホストするためのフォールバック。
    存在しないパスへのリクエストに対して index.html を返します。
    """
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)