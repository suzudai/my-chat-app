import os
import shutil
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# appモジュールをインポートするために、backendディレクトリをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import DEFAULT_CHAT_MODEL_ID


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    static_dir = os.path.join(backend_dir, "static")
    assets_dir = os.path.join(static_dir, "assets")

    os.makedirs(assets_dir, exist_ok=True)

    with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("<html><body>Test SPA</body></html>")
    with open(os.path.join(assets_dir, "test.css"), "w", encoding="utf-8") as f:
        f.write("body { color: red; }")

    with TestClient(app) as c:
        yield c

    shutil.rmtree(static_dir)


def test_chat_success(client):
    """/api/chatエンドポイントの成功ケースをテスト"""
    mock_response = MagicMock()
    mock_response.text = "こんにちは！"

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch("routers.simple_chat.get_model_client", return_value=mock_model) as mock_get_model_client:
        response = client.post("/api/chat", json={"message": "こんにちは", "model": DEFAULT_CHAT_MODEL_ID})

    assert response.status_code == 200
    assert response.json() == {"reply": "こんにちは！"}
    mock_get_model_client.assert_called_once_with(DEFAULT_CHAT_MODEL_ID)
    mock_model.generate_content.assert_called_once()


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
def test_chat_integration(client):
    """/api/chatエンドポイントの統合テスト（実際にAPIを呼び出す）"""
    response = client.post("/api/chat", json={"message": "こんにちは", "model": DEFAULT_CHAT_MODEL_ID})

    assert response.status_code == 200
    assert "reply" in response.json()
    assert isinstance(response.json()["reply"], str)
    assert len(response.json()["reply"]) > 0


def test_chat_api_error(client):
    """/api/chatエンドポイントでAPIエラーが発生するケースをテスト"""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API Error")

    with patch("routers.simple_chat.get_model_client", return_value=mock_model):
        response = client.post("/api/chat", json={"message": "エラーを発生させてください", "model": DEFAULT_CHAT_MODEL_ID})

    assert response.status_code == 500
    assert "detail" in response.json()
    assert response.json()["detail"] == "API Error"


def test_serve_spa_root(client):
    """ルートパスへのGETリクエストがindex.htmlを返すことをテスト"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_serve_spa_other_path(client):
    """存在しないパスへのGETリクエストがindex.htmlを返すことをテスト"""
    response = client.get("/some/random/path")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_serve_spa_api_path(client):
    """未定義メソッドのAPIパスはSPAフォールバックが返ることをテスト"""
    response = client.get("/api/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_serve_static_file(client):
    """静的ファイルへのリクエストが正しく処理されることをテスト"""
    response = client.get("/assets/test.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert response.text == "body { color: red; }"
