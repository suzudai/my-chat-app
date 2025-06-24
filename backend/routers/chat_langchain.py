from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
import os
import uuid
import msgpack
from datetime import datetime

from agents.deep_research import deep_research_agent
from agents.langgraph_test import search_agent
from models import get_available_models, is_valid_model, Model, get_model_instance, get_available_embedding_models, DEFAULT_CHAT_MODEL_ID
from chathistory.langgraph_chathistory import (
    chat_history, 
    get_session_title, 
    save_session_title,
    get_all_sessions,
    get_messages_for_session,
    delete_session
)

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str

class ChatResponse(BaseModel):
    reply: str
    updated_title: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" または "assistant"
    content: str
    timestamp: str

class ChatSession(BaseModel):
    thread_id: str
    title: str
    updated_at: str
    message_count: int
    last_message_at: str

class ChatWithHistoryRequest(BaseModel):
    message: str
    thread_id: str = "default"
    model_id: str = DEFAULT_CHAT_MODEL_ID

class ChatWithHistoryResponse(BaseModel):
    reply: str
    thread_id: str
    updated_title: Optional[str] = None

class UpdateTitleRequest(BaseModel):
    title: str

class Session(BaseModel):
    thread_id: str

@router.get("/models", response_model=List[Model])
async def get_models():
    """
    利用可能なチャットモデルのリストを返します。
    """
    return get_available_models()

@router.get("/embedding-models", response_model=List[Model])
async def get_embedding_models():
    """
    利用可能なエンベディングモデルのリストを返します。
    """
    return get_available_embedding_models()

# @router.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     """
#     ユーザーからのメッセージを受け取り、応答を生成します。
#     """
#     if not is_valid_model(request.model):
#         raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
#     try:
#         # 共通のモデル管理からインスタンスを取得
#         model = get_model_instance(request.model)
        
#         prompt = client.pull_prompt("test2")
#         messages = prompt.format_messages()
#         messages.append(("human", request.message))
#         response = model.invoke(messages)
#         return ChatResponse(reply=response.content)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat-with-history", response_model=ChatWithHistoryResponse)
async def chat_with_history(request: ChatWithHistoryRequest):
    """
    チャット履歴を保持した会話機能
    """
    try:
        print(f"📨 フロントエンドから受信したモデルID: {request.model_id}")  # デバッグ用ログ
        
        # モデルIDの妥当性をチェック
        if not is_valid_model(request.model_id):
            raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
        
        # チャット履歴機能を呼び出し（モデルIDを渡す）
        result = chat_history(request.message, request.thread_id, request.model_id)
        
        response = ChatWithHistoryResponse(
            reply=result.get("last_response", ""),
            thread_id=request.thread_id,
            updated_title=result.get("updated_title")
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理エラー: {str(e)}")

@router.get("/chat-sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    """
    全チャットセッションの一覧を取得します。
    """
    try:
        sessions = get_all_sessions()
        return [
            ChatSession(
                thread_id=session["thread_id"],
                title=session["title"],
                updated_at=session["updated_at"],
                message_count=session["message_count"],
                last_message_at=session["last_message_at"]
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"セッション取得エラー: {str(e)}")

@router.get("/chat-sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(session_id: str):
    """
    指定されたセッションIDの全メッセージを取得します。
    """
    try:
        messages = get_messages_for_session(session_id)
        return [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メッセージ取得エラー: {str(e)}")

@router.get("/chat-sessions/{session_id}/title")
async def get_session_title_endpoint(session_id: str):
    """
    指定されたセッションのタイトルを取得します。
    """
    try:
        title = get_session_title(session_id)
        if title is None:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        return {"title": title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイトル取得エラー: {str(e)}")

@router.put("/chat-sessions/{session_id}/title")
async def update_session_title(session_id: str, request: UpdateTitleRequest):
    """
    指定されたセッションのタイトルを更新します。
    """
    try:
        # タイトルの妥当性をチェック
        if not request.title or len(request.title.strip()) == 0:
            raise HTTPException(status_code=400, detail="タイトルが空です")
        
        if len(request.title) > 100:
            raise HTTPException(status_code=400, detail="タイトルが長すぎます（100文字以内）")
        
        # タイトルを保存
        save_session_title(session_id, request.title.strip())
        
        return {"message": "タイトルが更新されました", "title": request.title.strip()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイトル更新エラー: {str(e)}")

@router.delete("/chat-sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """
    指定されたセッションを削除します。
    """
    try:
        success = delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="セッションが見つかりません、または削除に失敗しました")
        
        return {"message": "セッションが削除されました"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"セッション削除エラー: {str(e)}")

@router.post("/chat-sessions")
async def create_chat_session():
    """
    新しいチャットセッションを作成します。
    """
    try:
        # 新しいUUIDを生成
        new_thread_id = str(uuid.uuid4())
        
        # 初期タイトルを設定
        initial_title = "チャットを開始中..."
        save_session_title(new_thread_id, initial_title)
        
        return {
            "thread_id": new_thread_id,
            "title": initial_title,
            "message": "新しいチャットセッションが作成されました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"セッション作成エラー: {str(e)}")

@router.post("/deep-research", response_model=ChatResponse)
async def deep_research(request: ChatRequest):
    """
    Deep Research Agent を使用した詳細な調査機能
    """
    if not is_valid_model(request.model):
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
    try:
        # 共通のモデル管理からインスタンスを取得
        model = get_model_instance(request.model)
        
        response = deep_research_agent(request.message, model)
        return ChatResponse(reply=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=ChatResponse)
async def search(request: ChatRequest):
    """
    Search Agent を使用した検索機能
    """
    if not is_valid_model(request.model):
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
    try:
        # 共通のモデル管理からインスタンスを取得
        model = get_model_instance(request.model)
        
        response = search_agent(request.message, model)
        return ChatResponse(reply=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 