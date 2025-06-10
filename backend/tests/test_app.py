import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import shutil

# appモジュールをインポートするために、backendディレクトリをsys.pathに追加
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    # テスト用のダミー静的ファイル/ディレクトリを作成
    static_dir = "static"
    assets_dir = os.path.join(static_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    with open(os.path.join(static_dir, "index.html"), "w") as f:
        f.write("<html><body>Test SPA</body></html>")
    with open(os.path.join(assets_dir, "test.css"), "w") as f:
        f.write("body { color: red; }")

    with TestClient(app) as c:
        yield c

    # テスト後にクリーンアップ
    shutil.rmtree(static_dir)

def test_chat_success(client):
    """/chatエンドポイントの成功ケースをテスト"""
    # model.generate_content のレスポンスをモック化
    mock_response = MagicMock()
    mock_response.text = "こんにちは！"

    # patchを使用して、genai.GenerativeModel('gemini-pro').generate_content をモック化
    with patch('app.model.generate_content', return_value=mock_response) as mock_generate_content:
        # /chatエンドポイントにPOSTリクエストを送信
        response = client.post("/chat", json={"message": "こんにちは", "model": "gemma-2-9b-it"})

        # ステータスコードが200であることを確認
        assert response.status_code == 200
        # レスポンスのJSONが期待通りであることを確認
        assert response.json() == {"reply": "こんにちは！"}
        # モックが正しく呼び出されたことを確認
        mock_generate_content.assert_called_once_with("こんにちは")

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
def test_chat_integration(client):
    """/chatエンドポイントの統合テスト（実際にAPIを呼び出す）"""
    # /chatエンドポイントにPOSTリクエストを送信
    response = client.post("/chat", json={"message": "こんにちは", "model": "gemini-1.5-flash"})

    # ステータスコードが200であることを確認
    assert response.status_code == 200
    # レスポンスのJSONにreplyキーがあり、その値が空でないことを確認
    assert "reply" in response.json()
    assert isinstance(response.json()["reply"], str)
    assert len(response.json()["reply"]) > 0

def test_chat_api_error(client):
    """/chatエンドポイントでAPIエラーが発生するケースをテスト"""
    # model.generate_content が例外を発生させるようにモック化
    with patch('app.model.generate_content', side_effect=Exception("API Error")) as mock_generate_content:
        # /chatエンドポイントにPOSTリクエストを送信
        response = client.post("/chat", json={"message": "エラーを発生させてください", "model": "gemma-2-9b-it"})

        # ステータスコードが500であることを確認
        assert response.status_code == 500
        # レスポンスのJSONにdetailキーが含まれていることを確認
        assert "detail" in response.json()
        assert response.json()["detail"] == "API Error"
        # モックが正しく呼び出されたことを確認
        mock_generate_content.assert_called_once_with("エラーを発生させてください")

def test_serve_spa_root(client):
    """ルートパスへのGETリクエストがindex.htmlを返すことをテスト"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']

def test_serve_spa_other_path(client):
    """存在しないパスへのGETリクエストがindex.htmlを返すことをテスト"""
    response = client.get("/some/random/path")
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']

def test_serve_spa_api_path(client):
    """APIパスへのGETリクエストが404を返すことをテスト"""
    response = client.get("/chat")
    assert response.status_code == 404

# このテストは静的ファイルが実際に存在する場合にのみ成功します
# CI/CD環境などでファイルが存在しない場合はスキップすることも検討してください
def test_serve_static_file(client):
    """静的ファイルへのリクエストが正しく処理されることをテスト"""
    response = client.get("/assets/test.css")
    assert response.status_code == 200
    assert "text/css" in response.headers['content-type']
    assert response.text == "body { color: red; }" 