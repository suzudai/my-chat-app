import React from 'react';

const AboutPage: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto">
        <div className="p-8 text-white">
          <h1 className="text-2xl font-bold mb-6">アプリケーションについて</h1>
          
          <div className="mb-8">
            <p className="text-lg mb-4">
              このアプリケーションは、Gemini AI を活用した複数のチャット機能を提供するプラットフォームです。
              React と FastAPI で構築されており、用途に応じて異なるチャット機能を選択できます。
            </p>
          </div>

          <div className="space-y-8">
            {/* Simple Chatの説明 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-300">🏠 Simple Chat</h2>
              <div className="mb-4">
                <h3 className="font-medium mb-2">機能：</h3>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li>シンプルな AI チャット機能</li>
                  <li>履歴は保存されません（セッション単位のやり取り）</li>
                  <li>複数のAIモデルから選択可能</li>
                </ul>
              </div>
              <div className="mb-4">
                <h3 className="font-medium mb-2">使い方：</h3>
                <ol className="list-decimal list-inside ml-4 space-y-1 text-gray-300">
                  <li>右上のモデル選択でお好みのAIモデルを選択</li>
                  <li>下部のテキストボックスに質問や会話内容を入力</li>
                  <li>送信ボタンまたはEnterキーで送信</li>
                  <li>AIからの回答が表示されます</li>
                </ol>
              </div>
              <div className="text-sm text-yellow-300">
                💡 このページは履歴が保存されないため、簡単な質問や一回限りの相談に最適です。
              </div>
            </section>

            {/* Chat with Historyの説明 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-green-300">💬 Chat with History</h2>
              <div className="mb-4">
                <h3 className="font-medium mb-2">機能：</h3>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li>会話履歴が自動的に保存されます</li>
                  <li>複数のチャットセッションを管理可能</li>
                  <li>セッションタイトルの自動生成・編集</li>
                  <li>過去の会話を継続可能</li>
                  <li>セッションの削除機能</li>
                </ul>
              </div>
              <div className="mb-4">
                <h3 className="font-medium mb-2">使い方：</h3>
                <ol className="list-decimal list-inside ml-4 space-y-1 text-gray-300">
                  <li>「新しいチャット」ボタンで新しいセッションを開始</li>
                  <li>左側のリストから過去のチャットセッションを選択可能</li>
                  <li>セッションタイトルをクリックして編集可能</li>
                  <li>ゴミ箱アイコンでセッションを削除</li>
                  <li>会話の文脈を維持しながら長期間の対話が可能</li>
                </ol>
              </div>
              <div className="text-sm text-yellow-300">
                💡 継続的な学習、プロジェクトの相談、長期間にわたる議論に最適です。
              </div>
            </section>

            {/* Chat with Agentsの説明 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-purple-300">🔍 Chat with Agents</h2>
              <div className="mb-4">
                <h3 className="font-medium mb-2">機能：</h3>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li>複数の情報源からの深度調査を実行</li>
                  <li>Elasticsearch + DuckDuckGoによる高度なWeb検索</li>
                  <li>最新ニュースとトレンド分析</li>
                  <li>事実検証と情報の信頼性評価</li>
                  <li>専門家の視点を含む包括的な分析</li>
                  <li>会話履歴の保存とセッション管理</li>
                </ul>
              </div>
              <div className="mb-4">
                <h3 className="font-medium mb-2">使い方：</h3>
                <ol className="list-decimal list-inside ml-4 space-y-1 text-gray-300">
                  <li>「新しいエージェントチャット」でセッションを開始</li>
                  <li>調査したいトピックについて詳細な質問を入力</li>
                  <li>AIが自動的に複数の情報源から調査を実行</li>
                  <li>構造化された包括的な調査レポートを取得</li>
                  <li>セッション履歴で過去の調査結果を確認可能</li>
                </ol>
              </div>
              <div className="text-sm text-yellow-300">
                💡 市場調査、技術動向分析、学術研究、業界レポート作成に最適です。
              </div>
            </section>

            {/* Chat with RAGの説明 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-teal-300">📚 Chat with RAG</h2>
              <div className="mb-4">
                <h3 className="font-medium mb-2">機能：</h3>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li>アップロードされた文書から情報を検索</li>
                  <li>文書に基づいた正確な回答を生成</li>
                  <li>複数文書の管理・選択機能</li>
                  <li>ファイルアップロード機能（PDF、DOCX、PPTX等）</li>
                  <li>特定の文書を指定した質問も可能</li>
                  <li>統一されたドキュメント管理UI</li>
                </ul>
              </div>
              <div className="mb-4">
                <h3 className="font-medium mb-2">使い方：</h3>
                <ol className="list-decimal list-inside ml-4 space-y-1 text-gray-300">
                  <li>左側パネルの「+」ボタンからファイルをアップロード</li>
                  <li>「📚 すべてのドキュメント」または特定の文書を選択</li>
                  <li>選択した文書または全文書を対象に質問を入力</li>
                  <li>AIが文書内容に基づいて回答を生成</li>
                  <li>不要な文書はゴミ箱アイコンで削除（2段階確認）</li>
                </ol>
              </div>
              <div className="mb-4">
                <h3 className="font-medium mb-2">UI改善：</h3>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li>Chat with Historyと統一されたUI設計</li>
                  <li>直感的な「+」ボタンでドキュメント追加</li>
                  <li>SVGアイコンによる洗練されたデザイン</li>
                  <li>2段階削除による誤操作防止</li>
                  <li>レスポンシブ対応とスムーズなアニメーション</li>
                </ul>
              </div>
              <div className="text-sm text-yellow-300">
                💡 社内文書の検索、学術論文の分析、マニュアルに関する質問などに最適です。
              </div>
            </section>

            {/* モデル選択の説明 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-orange-300">⚙️ AI モデル選択</h2>
              <div className="mb-4">
                <p className="text-gray-300 mb-2">
                  右上のドロップダウンメニューから、用途に応じて異なるAIモデルを選択できます：
                </p>
                <ul className="list-disc list-inside ml-4 space-y-1 text-gray-300">
                  <li><strong>Gemini 2.0 Flash Exp</strong>: 最新の高性能モデル（推奨）</li>
                  <li><strong>Gemini 1.5 Pro</strong>: バランスの取れた汎用モデル</li>
                  <li><strong>Gemini 1.5 Flash</strong>: 高速レスポンス重視</li>
                  <li>その他複数のモデルに対応</li>
                </ul>
              </div>
              <div className="text-sm text-yellow-300">
                💡 モデルによって回答の特性や処理速度が異なります。用途に応じて選択してください。
              </div>
            </section>

            {/* 技術情報 */}
            <section className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-red-300">🔧 技術情報</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
                <div>
                  <h3 className="font-medium mb-2">フロントエンド:</h3>
                  <ul className="list-disc list-inside ml-4 space-y-1 text-sm">
                    <li>React + TypeScript</li>
                    <li>Tailwind CSS</li>
                    <li>React Router</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium mb-2">バックエンド:</h3>
                  <ul className="list-disc list-inside ml-4 space-y-1 text-sm">
                    <li>FastAPI (Python)</li>
                    <li>LangChain & LangGraph</li>
                    <li>SQLite (チェックポイント保存)</li>
                    <li>Chroma DB (ベクトル検索)</li>
                    <li>Elasticsearch (Web検索)</li>
                    <li>DuckDuckGo (検索フォールバック)</li>
                  </ul>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-8 text-center text-gray-400 text-sm">
            <p>質問やご不明な点がございましたら、各機能ページでお気軽にお試しください。</p>
          </div>
        </div>
    </div>
  );
};

export default AboutPage; 