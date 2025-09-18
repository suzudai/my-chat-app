import sqlite3
import aiosqlite
from typing import Annotated, Literal, Any, List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from dotenv import load_dotenv
from datetime import datetime
import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import get_model_instance, DEFAULT_CHAT_MODEL_ID, is_valid_model
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import operator

load_dotenv()

# 同期SQLite接続（セッション管理用）
conn = sqlite3.connect("/code/my-chat-app/backend/chathistory/sqlite/chathistory.db", check_same_thread=False)

# 非同期SQLite接続とチェックポインター（遅延初期化）
checkpointer = None

async def get_checkpointer():
    """チェックポインターを取得（必要に応じて初期化）"""
    global checkpointer
    if checkpointer is None:
        async_conn = aiosqlite.connect("/code/my-chat-app/backend/chathistory/sqlite/chathistory.db")
        checkpointer = AsyncSqliteSaver(async_conn)
        await checkpointer.setup()
    return checkpointer

# セッションタイトル管理用のテーブルを確認（既に存在する場合はスキップ）
def setup_voting_session_titles_table():
    """Voting Graphセッションタイトル管理用のテーブルを作成・更新"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_titles (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER NOT NULL DEFAULT 0,
            last_message_at TIMESTAMP,
            category TEXT NOT NULL DEFAULT 'voting_graph'
        )
    """)
    conn.commit()

setup_voting_session_titles_table()

# Voting Graph用の状態定義
class VotingGraphState(TypedDict):
    messages: Annotated[list, add_messages]
    original_query: str
    agent_responses: Dict[str, str]  # エージェント名 -> 応答
    voting_results: Dict[str, Dict[str, int]]  # エージェント名 -> {候補: 得点}
    final_response: str
    current_phase: str

# 3つの異なる視点を持つエージェントの定義
AGENTS = {
    "logical_agent": {
        "name": "論理的思考エージェント",
        "system_prompt": """あなたは論理的思考を重視するAIエージェントです。
        - 事実に基づいた分析を行う
        - 論理的な根拠を明確に示す
        - 客観的で合理的な判断を重視する
        - データや証拠に基づいて結論を導く
        質問に対して論理的で構造化された回答を提供してください。"""
    },
    "empathetic_agent": {
        "name": "共感重視エージェント", 
        "system_prompt": """あなたは感情的・共感を重視するAIエージェントです。
        - 人間の感情や気持ちを理解する
        - 共感的で温かい対応を心がける
        - 相手の立場に立って考える
        - 心理的なサポートを提供する
        質問に対して共感的で人間らしい温かい回答を提供してください。"""
    },
    "concise_agent": {
        "name": "簡潔要約エージェント",
        "system_prompt": """あなたは簡潔・要約を重視するAIエージェントです。
        - 要点を明確に整理する
        - 無駄な情報を排除する
        - 分かりやすく簡潔な表現を使う
        - 効率的なコミュニケーションを重視する
        質問に対して簡潔で要点を押さえた回答を提供してください。"""
    }
}

def input_node(state: VotingGraphState):
    """入力受け取りノード"""
    if not state.get("current_phase"):
        return {
            "current_phase": "agent_responses", 
            "agent_responses": {},
            "voting_results": {},
            "final_response": ""
        }
    return state

def logical_agent_node(state: VotingGraphState):
    """論理的思考エージェント"""
    llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.1)
    
    system_message = SystemMessage(content=AGENTS["logical_agent"]["system_prompt"])
    user_query = state["original_query"]
    user_message = HumanMessage(content=user_query)
    
    messages = [system_message, user_message]
    response = llm.invoke(messages)
    
    agent_responses = state.get("agent_responses", {})
    agent_responses["logical_agent"] = response.content
    
    return {"agent_responses": agent_responses}

def empathetic_agent_node(state: VotingGraphState):
    """共感重視エージェント"""
    llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.7)
    
    system_message = SystemMessage(content=AGENTS["empathetic_agent"]["system_prompt"])
    user_query = state["original_query"]
    user_message = HumanMessage(content=user_query)
    
    messages = [system_message, user_message]
    response = llm.invoke(messages)
    
    agent_responses = state.get("agent_responses", {})
    agent_responses["empathetic_agent"] = response.content
    
    return {"agent_responses": agent_responses}

def concise_agent_node(state: VotingGraphState):
    """簡潔要約エージェント"""
    llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.3)
    
    system_message = SystemMessage(content=AGENTS["concise_agent"]["system_prompt"])
    user_query = state["original_query"]
    user_message = HumanMessage(content=user_query)
    
    messages = [system_message, user_message]
    response = llm.invoke(messages)
    
    agent_responses = state.get("agent_responses", {})
    agent_responses["concise_agent"] = response.content
    
    return {"agent_responses": agent_responses}

def voting_node(state: VotingGraphState):
    """投票集計ノード - 各エージェントが他の応答を評価"""
    llm = get_model_instance(DEFAULT_CHAT_MODEL_ID, temperature=0.1)
    
    agent_responses = state["agent_responses"]
    voting_results = {}
    
    # 各エージェントが他のエージェントの応答を評価
    for voter_agent, voter_info in AGENTS.items():
        if voter_agent not in agent_responses:
            continue
            
        # 投票用のプロンプト作成
        voting_prompt = f"""
あなたは{voter_info['name']}として、以下の質問に対する3つの異なる応答を評価してください。

質問: {state['original_query']}

応答候補:
1. 論理的思考エージェント: {agent_responses.get('logical_agent', '応答なし')}

2. 共感重視エージェント: {agent_responses.get('empathetic_agent', '応答なし')}

3. 簡潔要約エージェント: {agent_responses.get('concise_agent', '応答なし')}

重要な指示:
- 各応答を1-10点で評価し、その理由も説明してください
- あなた自身（{voter_info['name']}）の応答には投票できません（0点とする）
- 必ず以下のJSON形式のみで回答してください
- JSON以外の文章は一切含めないでください

{{
    "logical_agent": {{"score": 数値, "reason": "理由"}},
    "empathetic_agent": {{"score": 数値, "reason": "理由"}},
    "concise_agent": {{"score": 数値, "reason": "理由"}}
}}"""
        
        enhanced_system_prompt = voter_info["system_prompt"] + """

公平で客観的な評価を行ってください。
重要: 投票時は必ずJSONフォーマットで応答してください。
JSON以外の文章や説明は一切含めないでください。
あなた自身の応答には0点をつけてください。"""
        
        system_message = SystemMessage(content=enhanced_system_prompt)
        user_message = HumanMessage(content=voting_prompt)
        
        messages = [system_message, user_message]
        response = llm.invoke(messages)
        
        try:
            # JSONレスポンスをパース
            raw_response = response.content.strip()
            print(f"DEBUG: {voter_agent} raw response: {raw_response}")
            
            # JSON部分のみを抽出（```json で囲まれている場合の対処）
            if "```json" in raw_response:
                json_start = raw_response.find("```json") + 7
                json_end = raw_response.find("```", json_start)
                if json_end > json_start:
                    raw_response = raw_response[json_start:json_end].strip()
            elif "```" in raw_response:
                json_start = raw_response.find("```") + 3
                json_end = raw_response.find("```", json_start)
                if json_end > json_start:
                    raw_response = raw_response[json_start:json_end].strip()
            
            vote_data = json.loads(raw_response)
            
            # 自己投票禁止の確実な実装
            if voter_agent in vote_data:
                vote_data[voter_agent]["score"] = 0
                vote_data[voter_agent]["reason"] = "自己投票のため0点"
            
            print(f"DEBUG: {voter_agent} parsed vote_data: {vote_data}")
            voting_results[voter_agent] = vote_data
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"DEBUG: {voter_agent} JSON parse error: {e}")
            print(f"DEBUG: Raw response was: {response.content.strip()}")
            
            # JSONパースに失敗した場合のフォールバック
            fallback_data = {
                "logical_agent": {"score": 5, "reason": f"JSON解析エラー: {str(e)}"},
                "empathetic_agent": {"score": 5, "reason": f"JSON解析エラー: {str(e)}"},
                "concise_agent": {"score": 5, "reason": f"JSON解析エラー: {str(e)}"}
            }
            
            # 自己投票禁止
            if voter_agent in fallback_data:
                fallback_data[voter_agent]["score"] = 0
                fallback_data[voter_agent]["reason"] = "自己投票のため0点（フォールバック）"
            
            voting_results[voter_agent] = fallback_data
            print(f"DEBUG: {voter_agent} using fallback data: {fallback_data}")
    
    return {
        "voting_results": voting_results,
        "current_phase": "decision"
    }

def decision_node(state: VotingGraphState):
    """最終応答決定ノード - 最多票を得た応答を選択"""
    voting_results = state["voting_results"]
    agent_responses = state["agent_responses"]
    
    # 得点を集計
    total_scores = {"logical_agent": 0, "empathetic_agent": 0, "concise_agent": 0}
    
    for voter, votes in voting_results.items():
        for candidate, vote_info in votes.items():
            if candidate in total_scores:
                total_scores[candidate] += vote_info.get("score", 0)
    
    # 最高得点の応答を選択
    winner = max(total_scores, key=total_scores.get)
    winning_response = agent_responses.get(winner, "応答が見つかりません")
    
    # 投票結果の詳細を含む最終応答を作成
    result_summary = f"""
## 投票結果による最適応答

**選ばれた応答**: {AGENTS[winner]['name']}
**得点**: {total_scores[winner]}点

### 回答:
{winning_response}

### 投票詳細:
"""
    
    for agent, score in total_scores.items():
        result_summary += f"- {AGENTS[agent]['name']}: {score}点\n"
    
    result_summary += "\n### 各エージェントの評価理由:\n"
    for voter, votes in voting_results.items():
        result_summary += f"\n**{AGENTS[voter]['name']}の評価:**\n"
        for candidate, vote_info in votes.items():
            # 0点も含めて全ての評価を表示
            score = vote_info.get("score", 0)
            reason = vote_info.get("reason", "理由なし")
            result_summary += f"- {AGENTS[candidate]['name']}: {score}点 - {reason}\n"
    
    return {
        "final_response": result_summary,
        "current_phase": "output"
    }

def output_node(state: VotingGraphState):
    """出力返却ノード"""
    final_response = state["final_response"]
    
    # AIメッセージとして追加
    ai_message = AIMessage(content=final_response)
    
    return {
        "messages": [ai_message],
        "current_phase": "completed"
    }

# ルーティング関数
def route_after_input(state: VotingGraphState) -> Literal["logical_agent"]:
    return "logical_agent"

def route_after_agents(state: VotingGraphState) -> Literal["voting_node"]:
    # 全てのエージェントの応答が揃ったら投票に進む
    agent_responses = state.get("agent_responses", {})
    if len(agent_responses) >= 3:  # 3つのエージェント
        return "voting_node"
    return "voting_node"  # とりあえず投票に進む

def route_after_voting(state: VotingGraphState) -> Literal["decision_node"]:
    return "decision_node"

def route_after_decision(state: VotingGraphState) -> Literal["output_node"]:
    return "output_node"

def route_final(state: VotingGraphState) -> Literal["__end__"]:
    return "__end__"

# LangGraphの構築
async def create_voting_graph():
    """Voting Graph フローを構築"""
    workflow = StateGraph(VotingGraphState)
    
    # ノードを追加
    workflow.add_node("input_node", input_node)
    workflow.add_node("logical_agent", logical_agent_node)
    workflow.add_node("empathetic_agent", empathetic_agent_node)
    workflow.add_node("concise_agent", concise_agent_node)
    workflow.add_node("voting_node", voting_node)
    workflow.add_node("decision_node", decision_node)
    workflow.add_node("output_node", output_node)
    
    # エッジを追加
    workflow.set_entry_point("input_node")
    workflow.add_conditional_edges("input_node", route_after_input)
    
    # 順次実行でエージェントを実行（LangGraphの制約により並行処理は困難）
    workflow.add_edge("logical_agent", "empathetic_agent")
    workflow.add_edge("empathetic_agent", "concise_agent")
    workflow.add_conditional_edges("concise_agent", route_after_agents)
    
    workflow.add_conditional_edges("voting_node", route_after_voting)
    workflow.add_conditional_edges("decision_node", route_after_decision)
    workflow.add_conditional_edges("output_node", route_final)
    
    # AsyncSqliteSaverを取得
    checkpointer = await get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

# グラフインスタンス（非同期で初期化）
voting_graph = None

async def get_voting_graph():
    """Voting Graphインスタンスを取得（必要に応じて初期化）"""
    global voting_graph
    if voting_graph is None:
        voting_graph = await create_voting_graph()
    return voting_graph

# セッション管理関数
def save_voting_session_title(thread_id: str, title: str):
    """Voting Graphセッションのタイトルを保存"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO session_titles 
        (thread_id, title, updated_at, category)
        VALUES (?, ?, ?, ?)
    """, (thread_id, title, datetime.now().isoformat(), 'voting_graph'))
    conn.commit()

def get_voting_session_title(thread_id: str) -> str | None:
    """Voting Graphセッションのタイトルを取得"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title FROM session_titles 
        WHERE thread_id = ? AND category = 'voting_graph'
    """, (thread_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_voting_sessions() -> List[Dict[str, Any]]:
    """Voting Graphセッション一覧を取得"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT thread_id, title, updated_at, 
               COALESCE(message_count, 0) as message_count,
               COALESCE(last_message_at, updated_at) as last_message_at
        FROM session_titles 
        WHERE category = 'voting_graph'
        ORDER BY updated_at DESC
    """)
    results = cursor.fetchall()
    
    sessions = []
    for row in results:
        sessions.append({
            "thread_id": row[0],
            "title": row[1],
            "updated_at": row[2],
            "message_count": row[3],
            "last_message_at": row[4]
        })
    
    return sessions

async def get_voting_history(thread_id: str) -> List[Dict[str, Any]]:
    """Voting Graphセッションのメッセージ履歴を取得"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph = await get_voting_graph()
        state = await graph.aget_state(config)
        
        if not state or not state.values:
            return []
        
        messages = state.values.get("messages", [])
        formatted_messages = []
        
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "user" if msg.type == "human" else "assistant"
                formatted_messages.append({
                    "role": role,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                })
        
        return formatted_messages
    except Exception as e:
        print(f"履歴取得エラー: {e}")
        return []

def delete_voting_session(thread_id: str) -> bool:
    """Voting Graphセッションを削除"""
    try:
        cursor = conn.cursor()
        # セッションタイトルを削除
        cursor.execute("""
            DELETE FROM session_titles 
            WHERE thread_id = ? AND category = 'voting_graph'
        """, (thread_id,))
        
        # チェックポイントデータも削除
        cursor.execute("""
            DELETE FROM checkpoints 
            WHERE thread_id = ?
        """, (thread_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"セッション削除エラー: {e}")
        return False

def generate_voting_title(first_user_message: str, model_id: str = DEFAULT_CHAT_MODEL_ID) -> str:
    """最初のユーザーメッセージからタイトルを生成"""
    try:
        llm = get_model_instance(model_id, temperature=0.3)
        
        prompt = f"""以下のメッセージから、簡潔で分かりやすいタイトルを生成してください。
        タイトルは20文字以内で、内容を的確に表現するものにしてください。

        メッセージ: {first_user_message}

        タイトルのみを返してください。余計な説明は不要です。"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        title = response.content.strip()
        
        # タイトルが長すぎる場合は切り詰める
        if len(title) > 30:
            title = title[:27] + "..."
        
        return title
    except Exception as e:
        print(f"タイトル生成エラー: {e}")
        return "投票による協力チャット"

async def voting_graph_chat(query: str, thread_id: str = "default", model_id: str = DEFAULT_CHAT_MODEL_ID) -> dict[str, Any]:
    """Voting Graph チャット実行"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph = await get_voting_graph()
        
        # 初回メッセージかチェック
        existing_state = await graph.aget_state(config)
        is_first_message = not existing_state.values or not existing_state.values.get("messages")
        
        # ユーザーメッセージを作成
        user_message = HumanMessage(content=query)
        
        # 状態を更新して実行
        initial_state = {
            "messages": [user_message],
            "original_query": query,
            "agent_responses": {},
            "voting_results": {},
            "final_response": "",
            "current_phase": "input"
        }
        
        # グラフを実行
        result = await graph.ainvoke(initial_state, config)
        
        # 応答を取得
        ai_response = result.get("final_response", "応答を生成できませんでした")
        
        # 初回メッセージの場合、タイトルを生成・保存
        updated_title = None
        if is_first_message:
            title = generate_voting_title(query, model_id)
            save_voting_session_title(thread_id, title)
            updated_title = title
            
        # メッセージ数とタイムスタンプを更新
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE session_titles 
            SET message_count = message_count + 2,
                last_message_at = ?,
                updated_at = ?
            WHERE thread_id = ? AND category = 'voting_graph'
        """, (datetime.now().isoformat(), datetime.now().isoformat(), thread_id))
        conn.commit()
        
        return {
            "response": ai_response,
            "thread_id": thread_id,
            "updated_title": updated_title
        }
        
    except Exception as e:
        print(f"Voting Graph チャットエラー: {e}")
        return {
            "response": f"エラーが発生しました: {str(e)}",
            "thread_id": thread_id,
            "updated_title": None
        }

async def voting_graph_chat_stream(query: str, thread_id: str = "default", model_id: str = DEFAULT_CHAT_MODEL_ID):
    """Voting Graph チャットのストリーミング実行 - エージェントごとの応答をリアルタイム配信"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph = await get_voting_graph()
        
        # 初回メッセージかチェック
        existing_state = await graph.aget_state(config)
        is_first_message = not existing_state.values or not existing_state.values.get("messages")
        
        # ユーザーメッセージを作成
        user_message = HumanMessage(content=query)
        
        # 状態を更新して実行
        initial_state = {
            "messages": [user_message],
            "original_query": query,
            "agent_responses": {},
            "voting_results": {},
            "final_response": "",
            "current_phase": "input"
        }
        
        # 開始イベントを送信
        yield {
            "type": "start",
            "message": "投票によるチャット開始...",
            "thread_id": thread_id
        }
        
        # LangGraphストリーミングを使用してリアルタイム更新を取得
        async for chunk in graph.astream(initial_state, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                current_state = node_output
                
                # 各ノードの処理結果に応じてイベントを送信
                if node_name == "input_node":
                    yield {
                        "type": "phase_start",
                        "phase": "agents",
                        "message": "エージェントが応答を生成中..."
                    }
                
                elif node_name in ["logical_agent", "empathetic_agent", "concise_agent"]:
                    # エージェントの応答を取得
                    agent_responses = current_state.get("agent_responses", {})
                    if node_name in agent_responses:
                        agent_info = AGENTS.get(node_name, {})
                        yield {
                            "type": "agent_response",
                            "agent": node_name,
                            "agent_name": agent_info.get("name", node_name),
                            "response": agent_responses[node_name],
                            "message": f"{agent_info.get('name', node_name)}の応答が完了しました"
                        }
                
                elif node_name == "voting_node":
                    yield {
                        "type": "phase_start", 
                        "phase": "voting",
                        "message": "エージェント間で投票を実施中..."
                    }
                    
                    # 投票結果の詳細を送信
                    voting_results = current_state.get("voting_results", {})
                    if voting_results:
                        yield {
                            "type": "voting_results",
                            "voting_results": voting_results,
                            "message": "投票が完了しました"
                        }
                
                elif node_name == "decision_node":
                    yield {
                        "type": "phase_start",
                        "phase": "decision", 
                        "message": "最優秀応答を決定中..."
                    }
                
                elif node_name == "output_node":
                    # 最終応答を送信
                    final_response = current_state.get("final_response", "")
                    if final_response:
                        yield {
                            "type": "final_response",
                            "response": final_response,
                            "message": "投票による協力チャットが完了しました"
                        }
        
        # 初回メッセージの場合、タイトルを生成・保存
        updated_title = None
        if is_first_message:
            title = generate_voting_title(query, model_id)
            save_voting_session_title(thread_id, title)
            updated_title = title
            
            yield {
                "type": "title_updated",
                "title": title,
                "message": "セッションタイトルが生成されました"
            }
            
        # メッセージ数とタイムスタンプを更新
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE session_titles 
            SET message_count = message_count + 2,
                last_message_at = ?,
                updated_at = ?
            WHERE thread_id = ? AND category = 'voting_graph'
        """, (datetime.now().isoformat(), datetime.now().isoformat(), thread_id))
        conn.commit()
        
        # 完了イベントを送信
        yield {
            "type": "complete",
            "thread_id": thread_id,
            "updated_title": updated_title,
            "message": "すべての処理が完了しました"
        }
        
    except Exception as e:
        print(f"Voting Graph ストリーミングチャットエラー: {e}")
        yield {
            "type": "error",
            "message": f"エラーが発生しました: {str(e)}",
            "thread_id": thread_id
        }