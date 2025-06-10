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
cd "$BACKEND_DIR"

# Python環境の確認
if ! command -v python &> /dev/null; then
    echo "❌ エラー: Pythonが見つかりません"
    exit 1
fi

echo "🌐 サーバーを起動しています..."
echo "💡 アクセス方法: http://localhost:8000"
echo "⚠️  サーバーを停止するには Ctrl+C を押してください"
echo ""

# バックエンドサーバー起動
python app.py 