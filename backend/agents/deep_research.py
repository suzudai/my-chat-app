import sqlite3
from typing import Annotated, Literal, Any, List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.tools import tool
from datetime import datetime, timedelta
import json
import re
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import get_model_instance, DEFAULT_CHAT_MODEL_ID, is_valid_model
from langgraph.checkpoint.sqlite import SqliteSaver
import operator
import msgpack
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

load_dotenv()

conn = sqlite3.connect("/code/my-chat-app/backend/chathistory/sqlite/chathistory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
# データベーステーブルを初期化
checkpointer.setup()

# セッションタイトル管理用のテーブルを確認（既に存在する場合はスキップ）
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

setup_session_titles_table()

# シンプルな状態定義
class DeepResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    original_query: str
    current_phase: str

# LLMとツールの初期化
llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.1)

# Elasticsearch設定（環境変数から取得、デフォルト値を設定）
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "web_search")

try:
    es_client = Elasticsearch([ELASTICSEARCH_URL])
    # Elasticsearchの接続テスト
    if not es_client.ping():
        print("Warning: Elasticsearch connection failed, using DuckDuckGo as fallback")
        es_client = None
except Exception as e:
    print(f"Warning: Elasticsearch initialization failed: {e}, using DuckDuckGo as fallback")
    es_client = None

# フォールバック用のDuckDuckGo検索
ddg_search = DuckDuckGoSearchRun()

@tool
def web_search(query: str) -> str:
    """Web検索を実行して最新情報を取得する"""
    try:
        if es_client and es_client.ping():
            # Elasticsearch検索
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "description"],
                        "type": "best_fields"
                    }
                },
                "size": 5,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"timestamp": {"order": "desc"}}
                ]
            }
            
            response = es_client.search(index=ELASTICSEARCH_INDEX, body=search_body)
            hits = response.get('hits', {}).get('hits', [])
            
            if hits:
                formatted_results = []
                for hit in hits:
                    source = hit.get('_source', {})
                    formatted_results.append(
                        f"タイトル: {source.get('title', 'N/A')}\n"
                        f"内容: {source.get('content', source.get('description', 'N/A'))}\n"
                        f"URL: {source.get('url', 'N/A')}\n"
                        f"スコア: {hit.get('_score', 'N/A')}"
                    )
                return f"Elasticsearch検索結果 ({len(hits)}件):\n" + "\n---\n".join(formatted_results)
            else:
                # Elasticsearchで結果が見つからない場合のフォールバック
                return _fallback_web_search(query)
        else:
            # Elasticsearchが利用できない場合のフォールバック
            return _fallback_web_search(query)
    except Exception as e:
        print(f"Elasticsearch search error: {e}")
        return _fallback_web_search(query)

def _fallback_web_search(query: str) -> str:
    """フォールバック用のWeb検索（DuckDuckGo使用）"""
    try:
        results = ddg_search.run(query)
        return f"Web検索結果（DuckDuckGo）:\n{results}"
    except Exception as e:
        return f"検索エラー: {str(e)}。代替情報をご確認ください。"

@tool
def news_search(topic: str) -> str:
    """最新ニュースを検索する"""
    news_query = f"{topic} ニュース 最新 2025"
    try:
        if es_client and es_client.ping():
            # Elasticsearch検索（ニュース特化）
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": news_query,
                                    "fields": ["title^2", "content", "description"]
                                }
                            }
                        ],
                        "filter": [
                            {
                                "range": {
                                    "timestamp": {
                                        "gte": "now-30d"  # 過去30日以内
                                    }
                                }
                            }
                        ],
                        "should": [
                            {
                                "terms": {
                                    "category": ["news", "ニュース", "報道"]
                                }
                            }
                        ]
                    }
                },
                "size": 5,
                "sort": [
                    {"timestamp": {"order": "desc"}},
                    {"_score": {"order": "desc"}}
                ]
            }
            
            response = es_client.search(index=ELASTICSEARCH_INDEX, body=search_body)
            hits = response.get('hits', {}).get('hits', [])
            
            if hits:
                formatted_results = []
                for hit in hits:
                    source = hit.get('_source', {})
                    formatted_results.append(
                        f"タイトル: {source.get('title', 'N/A')}\n"
                        f"内容: {source.get('content', source.get('description', 'N/A'))}\n"
                        f"URL: {source.get('url', 'N/A')}\n"
                        f"日時: {source.get('timestamp', 'N/A')}"
                    )
                return f"Elasticsearchニュース検索結果 ({len(hits)}件):\n" + "\n---\n".join(formatted_results)
            else:
                return _fallback_news_search(news_query)
        else:
            return _fallback_news_search(news_query)
    except Exception as e:
        print(f"Elasticsearch news search error: {e}")
        return _fallback_news_search(news_query)

def _fallback_news_search(query: str) -> str:
    """フォールバック用のニュース検索（DuckDuckGo使用）"""
    try:
        results = ddg_search.run(query)
        return f"ニュース検索結果（DuckDuckGo）:\n{results}"
    except Exception as e:
        return f"ニュース検索エラー: {str(e)}"

tools = [web_search, news_search]
llm_with_tools = llm.bind_tools(tools)

def research_node(state: DeepResearchState):
    """情報収集を実行する"""
    system_prompt = """
    あなたは情報収集の専門家です。与えられた質問について、以下のツールを使用して情報を収集してください：

    1. web_search - Elasticsearchを使用した高度な情報検索（フォールバック：DuckDuckGo）
    2. news_search - Elasticsearchを使用した最新ニュース検索（フォールバック：DuckDuckGo）

    質問に関連する情報を幅広く収集し、複数の観点から情報を取得してください。
    Elasticsearchが利用できない場合は自動的にDuckDuckGoにフォールバックします。
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"質問: {state['original_query']}\n\n上記の質問について、ツールを使用して情報収集を開始してください。")
    ]
    
    try:
        response = llm_with_tools.invoke(messages)
    except Exception as e:
        print(f"Research error: {e}")
        response = AIMessage(content=f"情報収集中にエラーが発生しました: {str(e)}")
    
    return {
        "messages": [response],
        "current_phase": "research_complete"
    }

def analysis_node(state: DeepResearchState):
    """収集した情報を分析する"""
    system_prompt = """
    あなたは情報分析の専門家です。収集された情報を分析し、整理してください。

    分析の観点：
    1. 重要な事実の抽出
    2. 異なる情報源からの観点の整理
    3. 最新動向の特定
    4. 信頼性の評価

    分析結果は次の最終回答生成で使用されるため、要点を整理してください。
    """
    
    # 最新の研究結果を使用
    recent_messages = state['messages'][-3:]
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"質問: {state['original_query']}\n\n以下の情報を分析してください。")
    ] + recent_messages
    
    try:
        response = llm.invoke(messages)
    except Exception as e:
        print(f"Analysis error: {e}")
        response = AIMessage(content=f"分析中にエラーが発生しました: {str(e)}")
    
    return {
        "messages": [response],
        "current_phase": "analysis_complete"
    }

def final_answer_node(state: DeepResearchState):
    """最終回答を生成する"""
    system_prompt = """
    あなたは最終回答生成の専門家です。収集・分析された情報を基に、
    ユーザーの質問に対する包括的で分かりやすい最終回答を生成してください。

    【重要】回答は必ずマークダウン形式で構造化し、以下の形式に従ってください：

    ## 📝 概要
    質問に対する端的で明確な答え

    ## 🔍 詳細解説
    主要なポイントの詳細説明
    - **重要ポイント1**: 説明
    - **重要ポイント2**: 説明
    - **重要ポイント3**: 説明

    ## 📈 最新動向
    最新の情報やトレンド（2025年現在）

    ## ⚡ 重要ポイント
    > 覚えておくべき核心的な要点

    読みやすく、実用的な情報を提供してください。
    """
    
    # 分析結果を含む最新のメッセージを使用
    recent_messages = state['messages'][-5:]
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"質問: {state['original_query']}\n\n以下の調査・分析結果を基に、マークダウン形式で最終回答を作成してください。")
    ] + recent_messages
    
    try:
        response = llm.invoke(messages)
    except Exception as e:
        print(f"Final answer error: {e}")
        # エラー時のフォールバック回答
        response = AIMessage(content=f"""# 🔍 調査結果

**質問**: {state['original_query']}

## 📝 概要
申し訳ございませんが、詳細な調査中に技術的な問題が発生しました。

## 🔧 推奨事項
- より具体的な質問で再度お試しください
- しばらく時間をおいてから再度お試しください

**エラー詳細**: {str(e)}
""")
    
    return {
        "messages": [response],
        "current_phase": "final_answer_complete"
    }

# ツールノード
tool_node = ToolNode(tools=tools)

# シンプルなグラフ構築
builder = StateGraph(DeepResearchState)

# ノードを追加
builder.add_node("research", research_node)
builder.add_node("tool_execution", tool_node)
builder.add_node("analysis", analysis_node)
builder.add_node("final_answer", final_answer_node)

# エントリーポイント設定
builder.set_entry_point("research")

# シンプルなルーティング
def route_after_research(state: DeepResearchState) -> Literal["tool_execution", "analysis"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tool_execution"
    return "analysis"

def route_after_tools(state: DeepResearchState) -> Literal["analysis"]:
    return "analysis"

def route_after_analysis(state: DeepResearchState) -> Literal["final_answer"]:
    return "final_answer"

def route_final(state: DeepResearchState) -> Literal["__end__"]:
    return "__end__"

# エッジの追加
builder.add_conditional_edges(
    "research",
    route_after_research,
    {
        "tool_execution": "tool_execution",
        "analysis": "analysis"
    }
)

builder.add_conditional_edges(
    "tool_execution",
    route_after_tools,
    {"analysis": "analysis"}
)

builder.add_conditional_edges(
    "analysis",
    route_after_analysis,
    {"final_answer": "final_answer"}
)

builder.add_conditional_edges(
    "final_answer",
    route_final,
    {"__end__": END}
)

# グラフをコンパイル
deep_research_graph = builder.compile(checkpointer=checkpointer)

def save_deep_research_session_title(thread_id: str, title: str):
    """
    Deep Researchセッションのタイトルを保存または更新
    
    Parameters
    ----------
    thread_id : str
        セッションID
    title : str
        セッションタイトル
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
    """, (thread_id, title, now, now, now, "chat_with_agents", now))
    conn.commit()

def get_deep_research_session_title(thread_id: str) -> str | None:
    """
    Deep Researchセッションのタイトルを取得
    
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
    cursor.execute("SELECT title FROM session_titles WHERE thread_id = ? AND category = ?", (thread_id, "chat_with_agents"))
    result = cursor.fetchone()
    return result[0] if result else None

def get_deep_research_sessions() -> List[Dict[str, Any]]:
    """
    Deep Research（Chat with Agents）セッションの一覧を取得
    
    Returns
    -------
    List[Dict[str, Any]]
        セッション情報のリスト
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT thread_id, title, updated_at, message_count, last_message_at, category 
        FROM session_titles 
        WHERE category = ?
        ORDER BY last_message_at DESC, updated_at DESC
    """, ("chat_with_agents",))
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "thread_id": row[0],
            "title": row[1],
            "updated_at": row[2],
            "message_count": row[3],
            "last_message_at": row[4] if row[4] else row[2],
            "category": row[5]
        })
    
    return sessions

def get_deep_research_history(thread_id: str) -> List[Dict[str, Any]]:
    """
    指定されたDeep Researchセッションのメッセージ履歴を取得
    
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

        # 'messages'チャンネルからメッセージのリストを取得
        history_messages = checkpoint["channel_values"].get("messages", [])
        
        messages = []
        for i, msg in enumerate(history_messages):
            # BaseMessageオブジェクトのプロパティを元に辞書を作成
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            content = msg.content
            
            # タイムスタンプを生成（メッセージの順序を保持）
            base_time = datetime.now()
            timestamp = (base_time.replace(second=i, microsecond=0)).isoformat()

            messages.append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })

        return messages
        
    except Exception as e:
        print(f"Deep Researchメッセージ取得エラー: {e}")
        return []

def delete_deep_research_session(thread_id: str) -> bool:
    """
    指定されたDeep Researchセッションを削除
    
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
        # セッションタイトルを削除（カテゴリも確認）
        cursor = conn.cursor()
        cursor.execute("DELETE FROM session_titles WHERE thread_id = ? AND category = ?", (thread_id, "chat_with_agents"))
        
        # チェックポイントデータも削除
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Deep Researchセッション削除エラー: {e}")
        return False

def generate_deep_research_title(first_user_message: str, model_id: str = DEFAULT_CHAT_MODEL_ID) -> str:
    """
    Deep Researchチャットの最初のユーザーメッセージから要約タイトルを生成
    
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
            print(f"Deep Researchタイトル生成用モデル取得エラー: {e}, デフォルトモデルを使用")
            llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.0)
        
        # タイトル生成プロンプト
        title_prompt = f"""以下のDeep Research調査依頼から、30文字以内の簡潔なタイトルを生成してください。
調査内容を端的に表現し、チャット履歴のタイトルとして適切なものにしてください。

調査依頼: {first_user_message}

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

def deep_research_chat(query: str, thread_id: str = "default", model_id: str = DEFAULT_CHAT_MODEL_ID) -> dict[str, Any]:
    """
    Deep Research機能でチャット履歴を保持した会話
    
    Parameters
    ----------
    query : str
        ユーザーの調査依頼
    thread_id : str, optional
        会話スレッドのID（デフォルト: "default"）
    model_id : str, optional
        使用するモデルID（デフォルト: DEFAULT_CHAT_MODEL_ID）
    
    Returns
    -------
    dict[str, Any]
        調査結果（responseなどを含む）
    """
    # タイトル生成が必要かどうかをチェック
    existing_title = get_deep_research_session_title(thread_id)
    should_generate_title = (
        not existing_title or 
        existing_title in ['新しい調査', '調査を開始中...']
    )
    
    # Deep Research調査を実行
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # モデルIDの妥当性をチェック
        if not is_valid_model(model_id):
            model_id = DEFAULT_CHAT_MODEL_ID
        
        result = deep_research_graph.invoke(
            {"messages": [HumanMessage(content=query)], "original_query": query, "current_phase": "research"},
            config=config
        )
        
        # 最後のメッセージから回答を取得
        final_response = ""
        if result.get("messages"):
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                final_response = last_message.content
        
        # AI応答が成功した場合のみタイトルを生成・更新
        if should_generate_title and final_response:
            try:
                title = generate_deep_research_title(query, model_id)
                save_deep_research_session_title(thread_id, title)
                result["updated_title"] = title
            except Exception as e:
                print(f"Deep Researchタイトル生成エラー: {e}")
                
        # メッセージ数と最終メッセージ時刻を更新
        try:
            messages = get_deep_research_history(thread_id)
            message_count = len(messages)
            last_message_at = datetime.now()

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE session_titles
                SET message_count = ?, last_message_at = ?, updated_at = ?
                WHERE thread_id = ? AND category = ?
            """, (message_count, last_message_at, last_message_at, thread_id, "chat_with_agents"))
            conn.commit()
        except Exception as e:
            print(f"Deep Researchセッションメタデータ更新エラー: {e}")
        
        return {
            "response": final_response,
            "updated_title": result.get("updated_title")
        }
        
    except Exception as e:
        print(f"Deep Research実行エラー: {e}")
        return {
            "response": f"調査中にエラーが発生しました: {str(e)}",
            "updated_title": None
        }

if __name__ == "__main__":
    question = "AIの未来について教えてください。"
    print(deep_research_chat(question))