# 新規アプリケーション（ページ）追加手順

このドキュメントでは、新しい機能やページをこのプロジェクトに追加する際の基本的な手順を説明します。

## 概要

このプロジェクトは、フロントエンド（React）とバックエンド（FastAPI）が分離された構成になっています。

- **フロントエンド**: `frontend/` ディレクトリにあり、ReactとViteで構築されています。ルーティングは `react-router-dom` を使用したSPA（Single Page Application）です。
- **バックエンド**: `backend/` ディレクトリにあり、FastAPIで構築されています。`/api` プレフィックスでAPIを提供し、それ以外のパスではフロントエンドのビルド成果物（`index.html`）を返します。

## 手順

新しいページを追加する手順は、主にフロントエンド側の変更になります。必要に応じて、バックエンドに新しいAPIエンドポイントを追加します。

### 1. フロントエンドに新しいページを追加する

#### a. ページコンポーネントの作成

新しいページに対応するReactコンポーネントを `frontend/src/pages/` ディレクトリに作成します。

例として、`NewPage.tsx` を作成する場合：

```tsx:frontend/src/pages/NewPage.tsx
import React from 'react';

const NewPage: React.FC = () => {
  return (
    <div className="p-8 text-white">
      <h1 className="text-2xl font-bold mb-4">New Page</h1>
      <p>
        This is a new page.
      </p>
    </div>
  );
};

export default NewPage;
```

#### b. ルーティングの追加

作成したページコンポーネントをアプリケーションのルーティングに追加します。

`frontend/App.tsx` を編集して、新しいルートを追加します。

```tsx:frontend/App.tsx
// ... existing code ...
import HomePage from './src/pages/HomePage';
import AboutPage from './src/pages/AboutPage';
import NewPage from './src/pages/NewPage'; // 新しいページをインポート
import Layout from './src/Layout';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="new-page" element={<NewPage />} /> {/* 新しいルートを追加 */}
        </Route>
      </Routes>
    </Router>
  );
};

export default App;
```

#### c. (任意) ナビゲーションリンクの追加

全てのページからアクセスできるように、共通のナビゲーションバーにリンクを追加したい場合は `frontend/src/Layout.tsx` を編集します。

```tsx:frontend/src/Layout.tsx
// ... existing code ...
        <ul className="flex space-x-4">
          <li>
            <Link to="/" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              Chat
            </Link>
          </li>
          <li>
            <Link to="/about" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              About
            </Link>
          </li>
          <li>
            <Link to="/new-page" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              New Page {/* 新しいリンクを追加 */}
            </Link>
          </li>
        </ul>
// ... existing code ...
```

### 2. (任意) バックエンドに新しいAPIエンドポイントを追加する

新しいページでバックエンドのデータが必要な場合は、新しいAPIエンドポイントを作成します。

#### a. APIルーターの作成

`backend/routers/` ディレクトリに、機能ごとのルーターファイルを作成します。

例として `backend/routers/new_api.py` を作成する場合：

```python:backend/routers/new_api.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"message": "Hello from the new API"}
```

#### b. メインアプリケーションへのルーターの登録

作成したルーターを `backend/app.py` に登録し、`/api` プレフィックスを付けます。

```python:backend/app.py
// ... existing code ...
from routers import chat
from routers import new_api # 新しいルーターをインポート

app = FastAPI()

# APIルーターをインクルード
app.include_router(chat.router, prefix="/api")
app.include_router(new_api.router, prefix="/api/new") # 新しいルーターを登録

# ... existing code ...
```

これで、フロントエンドから `http://localhost:8000/api/new/data` にアクセスできるようになります。

### 3. 開発サーバーで確認

変更を保存したら、開発サーバーを再起動して動作を確認します。

1.  フロントエンドの変更を反映させるためにビルドします。
    ```bash
    npm run build --prefix frontend
    ```
2.  バックエンドサーバーを起動します。
    ```bash
    python backend/app.py
    ```
3.  ブラウザで新しいページ（例: `http://localhost:8000/new-page`）にアクセスして、正しく表示されることを確認します。

---
以上が、新しいアプリケーションを追加するための基本的な手順です。 