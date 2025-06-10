#!/bin/bash

# 開発モード用スクリプト
# フロントエンドとバックエンドを同時に起動します

set -e

echo "🛠️  開発モードを開始します..."

# スクリプトの実行ディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "📁 プロジェクトディレクトリ: $SCRIPT_DIR"

# フロントエンドの依存関係インストール
echo "📦 フロントエンドの依存関係をインストール中..."
cd "$FRONTEND_DIR"
npm install

# バックエンドを別のプロセスで起動
echo "🔥 バックエンドサーバーをバックグラウンドで起動中..."
cd "$BACKEND_DIR"
python app.py &
BACKEND_PID=$!

# 少し待ってからフロントエンド開発サーバーを起動
echo "⏳ バックエンドの起動を待機中..."
sleep 3

echo "⚛️  フロントエンド開発サーバーを起動中..."
cd "$FRONTEND_DIR"

echo ""
echo "🌐 開発サーバーのアクセス方法:"
echo "   フロントエンド: http://localhost:5173"
echo "   バックエンド: http://localhost:8000"
echo "⚠️  停止するには Ctrl+C を押してください"
echo ""

# Ctrl+Cでバックエンドプロセスも終了するように設定
trap "echo '🛑 開発サーバーを停止中...'; kill $BACKEND_PID 2>/dev/null; exit" INT

# フロントエンド開発サーバー起動
npm run dev 