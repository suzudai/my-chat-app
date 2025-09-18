#!/bin/bash

# チャットアプリケーションのビルドと起動スクリプト
# 使用方法: ./build-and-run.sh

set -e  # エラーが発生した場合にスクリプトを終了

echo "🚀 チャットアプリケーションのビルドと起動を開始します..."

# スクリプトの実行ディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "📁 プロジェクトディレクトリ: $SCRIPT_DIR"

# フロントエンドの依存関係インストール
echo "📦 フロントエンドの依存関係をインストール中..."
cd "$FRONTEND_DIR"
npm install

# フロントエンドのビルド
echo "🔨 フロントエンドをビルド中..."
npm run build

echo "✅ フロントエンドのビルドが完了しました"

# バックエンドに移動してサーバー起動
echo "🔥 バックエンドサーバーを起動中..."
echo "📁 バックエンドディレクトリに移動: $BACKEND_DIR"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ エラー: バックエンドディレクトリが見つかりません: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"
echo "✅ 現在のディレクトリ: $(pwd)"

# Python環境の確認
echo "🐍 Python環境を確認中..."
if ! command -v python &> /dev/null; then
    echo "❌ エラー: Pythonが見つかりません"
    exit 1
fi

echo "✅ Python バージョン: $(python --version)"

# app.pyファイルの存在確認
if [ ! -f "app.py" ]; then
    echo "❌ エラー: app.pyファイルが見つかりません"
    echo "📁 現在のディレクトリの内容:"
    ls -la
    exit 1
fi

echo "✅ app.pyファイルが見つかりました"

# 依存関係のチェック
echo "📦 Python依存関係をチェック中..."
if [ -f "requirements.txt" ]; then
    echo "📋 requirements.txtを確認中..."
    python -m pip install -r requirements.txt --quiet
    echo "✅ 依存関係のインストールが完了しました"
else
    echo "⚠️  requirements.txtが見つかりません。手動で依存関係を確認してください"
fi

# 既存のプロセスを終了
echo "🧹 既存のプロセスをクリーンアップ中..."

# Pythonアプリのプロセスを確認・終了
echo "🔍 Python app.pyプロセスを確認中..."
PYTHON_PIDS=$(pgrep -f "python.*app.py" || true)
if [ ! -z "$PYTHON_PIDS" ]; then
    echo "🛑 既存のPythonアプリプロセスを終了中: $PYTHON_PIDS"
    echo "$PYTHON_PIDS" | xargs -r kill -9
    sleep 3
    echo "✅ Pythonプロセスが終了しました"
else
    echo "✅ 実行中のPythonアプリプロセスはありません"
fi

# ポート8000を使用している既存のプロセスを終了
echo "🔍 ポート8000の使用状況を確認中..."
if command -v lsof &> /dev/null; then
    EXISTING_PIDS=$(lsof -ti:8000 || true)
    if [ ! -z "$EXISTING_PIDS" ]; then
        echo "🛑 ポート8000で実行中のプロセスを終了中: $EXISTING_PIDS"
        echo "$EXISTING_PIDS" | xargs -r kill -9
        sleep 3
        echo "✅ ポート8000のプロセスが終了しました"
    else
        echo "✅ ポート8000は使用されていません"
    fi
else
    echo "⚠️  警告: lsofコマンドが見つかりません。プロセス確認をスキップします"
fi

# 最終確認
echo "🔍 最終確認中..."
sleep 1

echo "🌐 サーバーを起動しています..."
echo "💡 アクセス方法: http://127.0.0.1:8000"
echo "⚠️  サーバーを停止するには Ctrl+C を押してください"
echo ""

# エラーハンドリング付きでバックエンドサーバー起動
echo "🔥 app.pyを実行中..."
if python app.py; then
    echo "✅ サーバーが正常に終了しました"
else
    echo "❌ サーバーの起動に失敗しました (終了コード: $?)"
    echo ""
    echo "🔍 トラブルシューティング:"
    echo "  1. Python依存関係を確認: pip install -r requirements.txt"
    echo "  2. エラーログを確認してください"
    echo "  3. ポート8000が他のプロセスで使用されていないか確認"
    echo ""
    exit 1
fi 