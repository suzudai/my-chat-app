import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# このリストはAPIの仕様として機能するため、こちらに残します。
AVAILABLE_MODELS = [
    "gemini-1.5-flash",
    "gemma-3-27b-it",
    "gemma-3n-e4b-it",
]

class ChatRequest(BaseModel):
    message: str
    model: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ユーザーからのメッセージを受け取り、指定されたモデルを使用して応答を生成します。
    """
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
    try:
        model = genai.GenerativeModel(request.model)
        prompt = f"以下の内容について、マークダウン形式で詳しく説明してください。\n\n{request.message}"
        response = model.generate_content(prompt)
        return ChatResponse(reply=response.text)
    except Exception as e:
        # エラーログを記録することが望ましい
        raise HTTPException(status_code=500, detail=str(e)) 