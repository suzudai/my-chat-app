# Gemini API Chat Application

これは、GoogleのGemini APIを利用した、React+FastAPI製のシンプルなチャットアプリケーションです。

## ✨ 特徴

-   **Dockerによるポータブルな開発環境**: `Dockerfile`により、どのマシンでも同じ開発環境を簡単に構築できます。
-   **ライブリロード**: ViteとUvicornによるホットリロードで、快適な開発体験を提供します。
-   **モデル選択**: 複数のGemini/GemmaモデルをUI上から切り替えて試すことができます。
-   **マークダウン対応**: AIの回答はマークダウンでレンダリングされ、コードブロックやリストもきれいに表示されます。

## 🛠️ 必要なもの

-   **Docker**: コンテナのビルドと実行に必要です。
-   **Google Gemini APIキー**: [こちら](https://ai.google.dev/gemini-api/docs/api-key)から取得できます。

## 🚀 開発環境の実行方法

1.  **APIキーの設定**

    プロジェクトのルートに `.env` ファイルを作成し、あなたのGemini APIキーを設定します。

    ```
    GEMINI_API_KEY="ここにあなたのAPIキーを貼り付けてください"
    ```

2.  **Dockerイメージのビルド**

    以下のコマンドを実行して、開発環境用のDockerイメージをビルドします。

    ```bash
    docker build -t my-chat-app-dev .
    ```

3.  **開発コンテナの起動**

    ビルドしたイメージを使って、開発用のコンテナを起動します。このコマンドは、ローカルのソースコードをコンテナにマウントするため、ローカルでコードを編集するとコンテナ内のアプリケーションに即座に反映されます。

    ```bash
    docker run -it -p 5173:5173 -p 8000:8000 --env-file .env -v "$(pwd):/app" --name chat-app-dev-container my-chat-app-dev
    ```
    *   **Windows (PowerShell)の場合:** `$(pwd)` の代わりに `(Get-Item -Path ".").FullName` を使用してください。

4.  **チャットを開始する**

    ブラウザで `http://localhost:5173` を開くと、チャットアプリケーションにアクセスできます。

## 🐳 Dockerコンテナの管理

-   **コンテナのログを確認する (バックグラウンド実行時):**
    ```bash
    docker logs -f chat-app-dev-container
    ```
-   **コンテナを停止する:**
    ```bash
    docker stop chat-app-dev-container
    ```
-   **停止したコンテナを再開する:**
    ```bash
    docker start -a chat-app-dev-container
    ```
-   **コンテナを削除する (停止してから実行):**
    ```bash
    docker rm chat-app-dev-container
    ```
