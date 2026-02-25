import operator
from typing import Annotated, Any, List, Dict
import sqlite3
import msgpack
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from dotenv import load_dotenv
load_dotenv()

# モデル管理モジュールからインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import get_model_instance, is_valid_model, DEFAULT_CHAT_MODEL_ID


class State(BaseModel):
    chat_history: Annotated[list[BaseMessage], operator.add] = Field(default_factory=list, description="チャット履歴")
    current_query: str = Field(default="", description="現在のクエリ")
    last_response: str = Field(default="", description="前回のレスポンス")
    current_role: str = Field(default="", description="現在の役割")
    model_id: str = Field(default=DEFAULT_CHAT_MODEL_ID, description="使用するモデルID")
    request_model_id: str = Field(default="", description="リクエストごとのモデルID")


db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "chathistory.db")

conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)
# データベーステーブルを初期化
checkpointer.setup()

def setup_session_titles_table():
    """セッションタイトル管理用のテーブルを作成・更新"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_titles (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 既存のテーブルにカラムを追加するためのエラーハンドリング
    try:
        cursor.execute("ALTER TABLE session_titles ADD COLUMN message_count INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    try:
        cursor.execute("ALTER TABLE session_titles ADD COLUMN last_message_at TIMESTAMP")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    try:
        cursor.execute("ALTER TABLE session_titles ADD COLUMN category TEXT NOT NULL DEFAULT 'chat_with_history'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    conn.commit()


workflow = StateGraph(State)

def answer_node(state: State) -> dict[str, Any]:
    query = state.current_query
    role = "チャットアシスタント"
    # request_model_id を優先して使用し、ない場合はデフォルト値を使用
    model_id = state.request_model_id if state.request_model_id else DEFAULT_CHAT_MODEL_ID

    print(f"🤖 受信したstate.request_model_id: {state.request_model_id}")  # デバッグ用ログ
    print(f"🤖 使用モデル: {model_id}")  # デバッグ用ログ

    # 動的にモデルインスタンスを取得
    try:
        if not is_valid_model(model_id):
            # 無効なモデルの場合はデフォルトを使用
            print(f"⚠️ 無効なモデルID: {model_id}, デフォルトに変更")
            model_id = DEFAULT_CHAT_MODEL_ID
        llm = get_model_instance(model_id, temperature=0.0)
        print(f"✅ モデルインスタンス作成成功: {model_id}")
    except Exception as e:
        print(f"❌ モデル取得エラー: {e}, デフォルトモデルを使用")
        llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.0)

    messages = [SystemMessage(content=f"あなたの役割: {role}")]
    messages.extend(state.chat_history)
    messages.append(HumanMessage(content=query))

    response = llm.invoke(messages)

    # model_idを返さないようにして、チェックポイントで上書きされないようにする
    return {"last_response": response.content, "chat_history": [HumanMessage(content=query), AIMessage(content=response.content)], "current_role": role}

workflow.add_node("answer_node", answer_node)

workflow.add_edge(START, "answer_node")
workflow.add_edge("answer_node", END)

graph = workflow.compile(checkpointer=checkpointer)

def generate_chat_title(first_user_message: str, model_id: str = DEFAULT_CHAT_MODEL_ID) -> str:
    """
    チャットの最初のユーザーメッセージから要約タイトルを生成
    
    Parameters
    ----------
    first_user_message : str
        最初のユーザーメッセージ
    model_id : str, optional
        使用するモデルID（デフォルト: DEFAULT_CHAT_MODEL_ID）
    
    Returns
    -------
    str
        生成されたタイトル（30文字以内）
    """
    try:
        # 動的にモデルインスタンスを取得
        try:
            if not is_valid_model(model_id):
                model_id = DEFAULT_CHAT_MODEL_ID
            llm = get_model_instance(model_id, temperature=0.0)
        except Exception as e:
            print(f"タイトル生成用モデル取得エラー: {e}, デフォルトモデルを使用")
            llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.0)
        
        # タイトル生成プロンプト
        title_prompt = f"""以下のメッセージから、30文字以内の簡潔なタイトルを生成してください。
内容を端的に表現し、チャット履歴のタイトルとして適切なものにしてください。

メッセージ: {first_user_message}

タイトルのみを出力してください。"""
        
        response = llm.invoke([HumanMessage(content=title_prompt)])
        title = response.content.strip()
        
        # 30文字を超える場合は省略
        if len(title) > 30:
            title = title[:27] + "..."
            
        return title
    except Exception as e:
        # エラーが発生した場合は最初のメッセージの冒頭を使用
        return first_user_message[:27] + ("..." if len(first_user_message) > 27 else "")

def save_session_title(thread_id: str, title: str, category: str = "chat_with_history"):
    """
    セッションのタイトルを保存または更新
    
    Parameters
    ----------
    thread_id : str
        セッションID
    title : str
        セッションタイトル
    category : str, optional
        セッションカテゴリ（デフォルト: "chat_with_history"）
        "chat_with_history" または "chat_with_agents"
    """
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO session_titles (thread_id, title, created_at, updated_at, message_count, last_message_at, category)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        ON CONFLICT(thread_id) DO UPDATE SET
            title = excluded.title,
            updated_at = ?,
            category = excluded.category
    """, (thread_id, title, now, now, now, category, now))
    conn.commit()

def get_session_title(thread_id: str) -> str | None:
    """
    セッションのタイトルを取得
    
    Parameters
    ----------
    thread_id : str
        セッションID
    
    Returns
    -------
    str | None
        セッションタイトル（存在しない場合はNone）
    """
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM session_titles WHERE thread_id = ?", (thread_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_all_sessions() -> List[Dict[str, Any]]:
    """
    全チャットセッションの一覧を取得
    
    Returns
    -------
    List[Dict[str, Any]]
        セッション情報のリスト（thread_id, title, updated_at, message_count, last_message_at, category）
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT thread_id, title, updated_at, message_count, last_message_at, category 
        FROM session_titles 
        ORDER BY last_message_at DESC, updated_at DESC
    """)
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "thread_id": row[0],
            "title": row[1],
            "updated_at": row[2],
            "message_count": row[3],
            "last_message_at": row[4] if row[4] else row[2], # Fallback to updated_at
            "category": row[5] if row[5] else "chat_with_history"  # デフォルト値
        })
    
    return sessions

def get_sessions_by_category(category: str) -> List[Dict[str, Any]]:
    """
    指定されたカテゴリのチャットセッション一覧を取得
    
    Parameters
    ----------
    category : str
        セッションカテゴリ（"chat_with_history" または "chat_with_agents"）
    
    Returns
    -------
    List[Dict[str, Any]]
        セッション情報のリスト（thread_id, title, updated_at, message_count, last_message_at, category）
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT thread_id, title, updated_at, message_count, last_message_at, category 
        FROM session_titles 
        WHERE category = ?
        ORDER BY last_message_at DESC, updated_at DESC
    """, (category,))
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "thread_id": row[0],
            "title": row[1],
            "updated_at": row[2],
            "message_count": row[3],
            "last_message_at": row[4] if row[4] else row[2], # Fallback to updated_at
            "category": row[5]
        })
    
    return sessions

def get_messages_for_session(thread_id: str) -> List[Dict[str, Any]]:
    """
    指定されたセッションのメッセージ履歴を取得（信頼性の高い方法に修正）
    
    Parameters
    ----------
    thread_id : str
        セッションID
    
    Returns
    -------
    List[Dict[str, Any]]
        メッセージ履歴のリスト
    """
    try:
        # 特定のスレッドの最新のチェックポイントを取得
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint = checkpointer.get(config)

        if not checkpoint or "channel_values" not in checkpoint:
            return []

        # 'chat_history'チャンネルからメッセージのリストを取得
        history_messages = checkpoint["channel_values"].get("chat_history", [])
        
        messages = []
        for msg in history_messages:
            # BaseMessageオブジェクトのプロパティを元に辞書を作成
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            content = msg.content
            
            # タイムスタンプはチェックポイントから取得できないため、現在時刻を使用
            timestamp = datetime.now().isoformat()

            messages.append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })

        return messages
        
    except Exception as e:
        print(f"メッセージ取得エラー (get_messages_for_session): {e}")
        return []

def delete_session(thread_id: str) -> bool:
    """
    指定されたセッションを削除
    
    Parameters
    ----------
    thread_id : str
        削除するセッションID
    
    Returns
    -------
    bool
        削除成功の可否
    """
    try:
        # セッションタイトルを削除
        cursor = conn.cursor()
        cursor.execute("DELETE FROM session_titles WHERE thread_id = ?", (thread_id,))
        
        # チェックポイントデータも削除
        # LangGraphのSqliteSaverから直接削除
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"セッション削除エラー: {e}")
        return False

def chat_history(query: str, thread_id: str = "default", model_id: str = DEFAULT_CHAT_MODEL_ID, category: str = "chat_with_history") -> dict[str, Any]:
    """
    チャット履歴を保持した会話機能
    
    Parameters
    ----------
    query : str
        ユーザーの質問
    thread_id : str, optional
        会話スレッドのID（デフォルト: "default"）
    model_id : str, optional
        使用するモデルID（デフォルト: DEFAULT_CHAT_MODEL_ID）
    category : str, optional
        セッションカテゴリ（デフォルト: "chat_with_history"）
    
    Returns
    -------
    dict[str, Any]
        グラフの実行結果（last_responseなどを含む）
    """
    # タイトル生成が必要かどうかをチェック
    existing_title = get_session_title(thread_id)
    should_generate_title = (
        not existing_title or 
        existing_title in ['新しいチャット', 'チャットを開始中...']
    )
    
    # AI応答を生成（request_model_idのみ渡す）
    result = graph.invoke(
        {"current_query": query, "request_model_id": model_id},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # AI応答が成功した場合のみタイトルを生成・更新
    if should_generate_title and result.get("last_response"):
        try:
            title = generate_chat_title(query, model_id)
            save_session_title(thread_id, title, category)
            result["updated_title"] = title
        except Exception as e:
            print(f"タイトル生成エラー: {e}")
            
    # メッセージ数と最終メッセージ時刻を更新
    try:
        messages = get_messages_for_session(thread_id)
        message_count = len(messages)
        last_message_at = datetime.now()

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE session_titles
            SET message_count = ?, last_message_at = ?, updated_at = ?
            WHERE thread_id = ?
        """, (message_count, last_message_at, last_message_at, thread_id))
        conn.commit()
    except Exception as e:
        print(f"セッションメタデータ更新エラー: {e}")
    
    return result

# すべての関数定義が完了した後に初期化を実行
setup_session_titles_table()
