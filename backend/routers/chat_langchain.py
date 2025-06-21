from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
import os

from agents.deep_research import deep_research_agent
from agents.langgraph_test import search_agent
from models import get_available_models, is_valid_model, Model, get_model_instance, get_available_embedding_models

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str

class ChatResponse(BaseModel):
    reply: str

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

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ユーザーからのメッセージを受け取り、応答を生成します。
    """
    if not is_valid_model(request.model):
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
    try:
        # 共通のモデル管理からインスタンスを取得
        model = get_model_instance(request.model)
        
        prompt = client.pull_prompt("test2")
        messages = prompt.format_messages()
        messages.append(("human", request.message))
        response = model.invoke(messages)
        return ChatResponse(reply=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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