# モデル管理の統一化とGemini 2.5モデルの追加

**実施日:** 2025-01-29  
**タスク概要:** 全てのチャットアプリで共通のモデル管理を実装し、Gemini 2.5 ProとGemini 2.5 Flashを追加

## 実施内容

### 1. 共通モデル定義ファイルの作成

**ファイル:** `backend/models.py`
- 全アプリで共通使用する利用可能モデル一覧を定義
- 新しく追加されたモデル：
  - `gemini-2.5-flash`: Gemini 2.5 Flash
  - `gemini-2.5-pro`: Gemini 2.5 Pro
- 従来のモデル：
  - `gemini-1.5-flash`: Gemini 1.5 Flash
  - `gemma-3-27b-it`: Gemma 3 (37B)
  - `gemma-3n-e4b-it`: Gemma 3N (E4B)

### 2. 各ルーターの更新

#### 2.1 `backend/routers/chat.py`
- 共通モデル定義を使用するように変更
- モデル一覧取得エンドポイント `/models` を追加
- モデル検証に共通関数を使用

#### 2.2 `backend/routers/chat_langchain.py`
- 共通モデル定義を使用するように更新
- 既存の `/models` エンドポイントを共通定義に統一

#### 2.3 `backend/routers/chat_langchain_rag.py`
- 共通モデル定義を使用するように更新
- モデル一覧取得エンドポイント `/models` を追加
- RAGチャット機能でモデル検証を追加

### 3. RAGフローの改善

**ファイル:** `backend/langchain_rag/langchain_rag.py`
- `vector_search_flow()` 関数にモデルパラメータを追加
- `get_rag_flow()` 関数にモデルパラメータを追加
- 動的なモデル選択をサポート

### 4. フロントエンドの改善

**ファイル:** `frontend/src/Layout.tsx`
- デフォルトモデル選択ロジックを改善
- 優先順位：`gemini-2.5-pro` > `gemini-2.5-flash` > `gemini-1.5-flash`
- モデル取得の処理を最適化

## 利用可能なAPIエンドポイント

以下の全てのエンドポイントで共通のモデル一覧が取得可能：

1. `/api/models` - 基本チャット
2. `/api/langchain/models` - LangChainチャット  
3. `/api/langchainchatrag/models` - LangChain RAGチャット

## 変更の利点

1. **統一性**: 全てのアプリで同じモデル定義を使用
2. **保守性**: モデルの追加・削除が一箇所で管理可能
3. **拡張性**: 新しいモデルを簡単に追加可能
4. **最新モデル**: Gemini 2.5シリーズの利用が可能

## 動作確認項目

- [ ] 全チャットページでモデル選択が正常に動作
- [ ] 新しいGeminiモデルが選択肢に表示される
- [ ] デフォルトでGemini 2.5 Proが選択される
- [ ] 各チャット機能で選択したモデルが正常に使用される
- [ ] RAGチャットで選択したモデルが適用される

## 技術的な改善点

- モデル定義の中央集権化
- 型安全性の向上（Pydanticモデル使用）
- エラーハンドリングの統一
- コードの重複排除 