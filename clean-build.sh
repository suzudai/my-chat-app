#!/bin/bash

# クリーンビルドスクリプト
# node_modules と static ディレクトリを削除してから再ビルドします

set -e

echo "🧹 クリーンビルドを開始します..."

# スクリプトの実行ディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "📁 プロジェクトディレクトリ: $SCRIPT_DIR"

# フロントエンドのクリーンアップ
echo "🗑️  フロントエンドのクリーンアップ中..."
cd "$FRONTEND_DIR"
if [ -d "node_modules" ]; then
    echo "   node_modules を削除中..."
    rm -rf node_modules
fi

# バックエンドのstaticディレクトリをクリーンアップ
if [ -d "$BACKEND_DIR/static" ]; then
    echo "   backend/static を削除中..."
    rm -rf "$BACKEND_DIR/static"
fi

# 依存関係を再インストール
echo "📦 依存関係を再インストール中..."
npm install

# フロントエンドをビルド
echo "🔨 フロントエンドをビルド中..."
npm run build

echo "✅ クリーンビルドが完了しました"

# バックエンドに移動してサーバー起動
echo "🔥 バックエンドサーバーを起動中..."
cd "$BACKEND_DIR"

echo "🌐 サーバーを起動しています..."
echo "💡 アクセス方法: http://localhost:8000"
echo "⚠️  サーバーを停止するには Ctrl+C を押してください"
echo ""

# バックエンドサーバー起動
python app.py 