from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any
from pydantic import BaseModel
import uuid
from datetime import datetime
import json

# Voting Graph エージェントをインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.voting_graph import (
    voting_graph_chat,
    voting_graph_chat_stream,
    get_voting_history,
    get_voting_sessions,
    get_voting_session_title,
    save_voting_session_title,
    delete_voting_session
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

@router.post("/voting-graph-chat", response_model=ChatResponse)
async def voting_graph_chat_endpoint(request: ChatRequest):
    """Voting Graph エージェントとチャットする（新規セッション）"""
    try:
        # 新しいスレッドIDを生成
        thread_id = str(uuid.uuid4())
        
        # Voting Graph エージェントを実行（統一されたDB使用）
        result = await voting_graph_chat(request.message, thread_id=thread_id, model_id=request.model)
        
        # 結果から応答を取得
        ai_response = result.get("response", "")
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="Voting Graph エージェントからの応答が取得できませんでした")
        
        return ChatResponse(
            reply=ai_response,
            thread_id=thread_id,
            updated_title=result.get("updated_title")
        )
        
    except Exception as e:
        print(f"Voting Graph チャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Voting Graph エラー: {str(e)}")

@router.post("/voting-graph-chat-stream")
async def voting_graph_chat_stream_endpoint(request: ChatRequest):
    """Voting Graph エージェントとのストリーミングチャット（新規セッション）"""
    try:
        # 新しいスレッドIDを生成
        thread_id = str(uuid.uuid4())
        
        async def generate_stream():
            try:
                async for chunk in voting_graph_chat_stream(request.message, thread_id=thread_id, model_id=request.model):
                    # SSE形式でデータを送信
                    data = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                
                # ストリーム終了シグナル
                yield f"data: {json.dumps({'type': 'end', 'thread_id': thread_id})}\n\n"
                
            except Exception as e:
                error_data = json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # nginx用のバッファリング無効化
            }
        )
        
    except Exception as e:
        print(f"Voting Graph ストリーミングチャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Voting Graph ストリーミングエラー: {str(e)}")

@router.post("/voting-graph-sessions", response_model=CreateSessionResponse)
async def create_voting_graph_session():
    """新しいVoting Graphセッションを作成"""
    thread_id = str(uuid.uuid4())
    title = "投票による協力チャット..."
    
    try:
        save_voting_session_title(thread_id, title)
        return CreateSessionResponse(thread_id=thread_id, title=title)
    except Exception as e:
        print(f"セッション作成エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの作成に失敗しました")

@router.get("/voting-graph-sessions", response_model=List[SessionResponse])
async def get_voting_graph_sessions_endpoint():
    """Voting Graphセッション一覧を取得"""
    try:
        sessions = get_voting_sessions()
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

@router.get("/voting-graph-sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_voting_graph_session_messages(session_id: str):
    """特定のVoting Graphセッションのメッセージ履歴を取得"""
    try:
        # チェックポイントから履歴を取得
        messages = await get_voting_history(session_id)
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

@router.delete("/voting-graph-sessions/{session_id}")
async def delete_voting_graph_session_endpoint(session_id: str):
    """Voting Graphセッションを削除"""
    try:
        # 統一されたDB管理で削除
        success = delete_voting_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        return {"message": "セッションが削除されました"}
    except Exception as e:
        print(f"セッション削除エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの削除に失敗しました")

@router.put("/voting-graph-sessions/{session_id}/title")
async def update_voting_graph_session_title(session_id: str, request: TitleUpdateRequest):
    """Voting Graphセッションのタイトルを更新"""
    try:
        save_voting_session_title(session_id, request.title)
        return {"message": "タイトルが更新されました"}
    except Exception as e:
        print(f"タイトル更新エラー: {e}")
        raise HTTPException(status_code=500, detail="タイトルの更新に失敗しました")

@router.post("/voting-graph-sessions/{session_id}/chat", response_model=ChatResponse)
async def continue_voting_graph_chat(session_id: str, request: ChatRequest):
    """既存のVoting Graphセッションで会話を続ける"""
    try:
        # セッションが存在するかチェック
        existing_title = get_voting_session_title(session_id)
        if not existing_title:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # Voting Graph エージェントを実行（既存のthread_idで継続）
        result = await voting_graph_chat(request.message, thread_id=session_id, model_id=request.model)
        
        # 結果から応答を取得
        ai_response = result.get("response", "")
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="Voting Graph エージェントからの応答が取得できませんでした")
        
        return ChatResponse(
            reply=ai_response,
            thread_id=session_id,
            updated_title=result.get("updated_title")
        )
        
    except Exception as e:
        print(f"Voting Graph 継続チャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Voting Graph エラー: {str(e)}")

@router.post("/voting-graph-sessions/{session_id}/chat-stream")
async def continue_voting_graph_chat_stream(session_id: str, request: ChatRequest):
    """既存のVoting Graphセッションでストリーミングチャットを続ける"""
    try:
        # セッションが存在するかチェック
        existing_title = get_voting_session_title(session_id)
        if not existing_title:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        async def generate_stream():
            try:
                async for chunk in voting_graph_chat_stream(request.message, thread_id=session_id, model_id=request.model):
                    # SSE形式でデータを送信
                    data = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                
                # ストリーム終了シグナル
                yield f"data: {json.dumps({'type': 'end', 'thread_id': session_id})}\n\n"
                
            except Exception as e:
                error_data = json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        print(f"Voting Graph 継続ストリーミングチャットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Voting Graph ストリーミングエラー: {str(e)}") 