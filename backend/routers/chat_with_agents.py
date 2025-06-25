from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel
import uuid
from datetime import datetime

# Deep Research エージェントをインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.deep_research import (
    deep_research_chat,
    get_deep_research_history,
    get_deep_research_sessions,
    get_deep_research_session_title,
    save_deep_research_session_title,
    delete_deep_research_session
)
from models import DEFAULT_CHAT_MODEL_ID

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str = DEFAULT_CHAT_MODEL_ID

class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    updated_title: str | None = None

class SessionResponse(BaseModel):
    thread_id: str
    title: str
    updated_at: str
    message_count: int
    last_message_at: str

class CreateSessionResponse(BaseModel):
    thread_id: str
    title: str

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class TitleUpdateRequest(BaseModel):
    title: str

@router.post("/deep-research-chat", response_model=ChatResponse)
async def deep_research_chat_endpoint(request: ChatRequest):
    """Deep Research エージェントとチャットする（新規セッション）"""
    try:
        # 新しいスレッドIDを生成
        thread_id = str(uuid.uuid4())
        
        # Deep Research エージェントを実行（統一されたDB使用）
        result = deep_research_chat(request.message, thread_id=thread_id, model_id=request.model)
        
        # 結果から応答を取得
        ai_response = result.get("response", "")
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="Deep Research エージェントからの応答が取得できませんでした")
        
        return ChatResponse(
            reply=ai_response,
            thread_id=thread_id,
            updated_title=result.get("updated_title")
        )
        
    except Exception as e:
        print(f"Deep Research チャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Deep Research エラー: {str(e)}")

@router.post("/deep-research-sessions", response_model=CreateSessionResponse)
async def create_deep_research_session():
    """新しいDeep Researchセッションを作成"""
    thread_id = str(uuid.uuid4())
    title = "調査を開始中..."
    
    try:
        save_deep_research_session_title(thread_id, title)
        return CreateSessionResponse(thread_id=thread_id, title=title)
    except Exception as e:
        print(f"セッション作成エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの作成に失敗しました")

@router.get("/deep-research-sessions", response_model=List[SessionResponse])
async def get_deep_research_sessions_endpoint():
    """Deep Researchセッション一覧を取得"""
    try:
        sessions = get_deep_research_sessions()
        return [
            SessionResponse(
                thread_id=session["thread_id"],
                title=session["title"],
                updated_at=session["updated_at"],
                message_count=session["message_count"],
                last_message_at=session["last_message_at"]
            )
            for session in sessions
        ]
    except Exception as e:
        print(f"セッション取得エラー: {e}")
        raise HTTPException(status_code=500, detail="セッション一覧の取得に失敗しました")

@router.get("/deep-research-sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_deep_research_session_messages(session_id: str):
    """特定のDeep Researchセッションのメッセージ履歴を取得"""
    try:
        # チェックポイントから履歴を取得
        messages = get_deep_research_history(session_id)
        return [
            MessageResponse(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in messages
        ]
    except Exception as e:
        print(f"メッセージ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="メッセージの取得に失敗しました")

@router.delete("/deep-research-sessions/{session_id}")
async def delete_deep_research_session_endpoint(session_id: str):
    """Deep Researchセッションを削除"""
    try:
        # 統一されたDB管理で削除
        success = delete_deep_research_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        return {"message": "セッションが削除されました"}
    except Exception as e:
        print(f"セッション削除エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの削除に失敗しました")

@router.put("/deep-research-sessions/{session_id}/title")
async def update_deep_research_session_title(session_id: str, request: TitleUpdateRequest):
    """Deep Researchセッションのタイトルを更新"""
    try:
        save_deep_research_session_title(session_id, request.title)
        return {"message": "タイトルが更新されました"}
    except Exception as e:
        print(f"タイトル更新エラー: {e}")
        raise HTTPException(status_code=500, detail="タイトルの更新に失敗しました")

@router.post("/deep-research-sessions/{session_id}/chat", response_model=ChatResponse)
async def continue_deep_research_chat(session_id: str, request: ChatRequest):
    """既存のDeep Researchセッションで会話を続ける"""
    try:
        # セッションが存在するかチェック
        existing_title = get_deep_research_session_title(session_id)
        if not existing_title:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # Deep Research エージェントを実行（既存のthread_idで継続）
        result = deep_research_chat(request.message, thread_id=session_id, model_id=request.model)
        
        # 結果から応答を取得
        ai_response = result.get("response", "")
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="Deep Research エージェントからの応答が取得できませんでした")
        
        return ChatResponse(
            reply=ai_response,
            thread_id=session_id,
            updated_title=result.get("updated_title")
        )
        
    except Exception as e:
        print(f"Deep Research 継続チャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Deep Research エラー: {str(e)}") 