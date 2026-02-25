from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import importlib
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

load_dotenv()

app = FastAPI()

# 環境変数 GEMINI_API_KEY を設定
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("警告: 環境変数 'GEMINI_API_KEY' が設定されていません。")
else:
    genai.configure(api_key=api_key)


def include_router_if_available(module_name: str, prefix: str = "/api") -> None:
    """依存関係が揃っているルーターのみを安全に読み込む。"""
    try:
        module = importlib.import_module(f"routers.{module_name}")
        app.include_router(module.router, prefix=prefix)
    except Exception as e:
        print(f"警告: routers.{module_name} の読み込みをスキップしました: {e}")


# APIルーターをインクルード
include_router_if_available("simple_chat", "/api")
include_router_if_available("new_api", "/api/new")
include_router_if_available("chat_with_history", "/api/langchain")
include_router_if_available("chat_with_rag", "/api/langchainchatrag")
include_router_if_available("chat_with_agents", "/api/deep-research")
include_router_if_available("voting_graph", "/api/voting-graph")

# Viteによってビルドされた静的ファイルを配信します。
os.makedirs(os.path.join(static_file_dir, "assets"), exist_ok=True)
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
