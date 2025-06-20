from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
import os
from dotenv import load_dotenv
from agents.deep_research import deep_research_agent
from agents.langgraph_test import search_agent
load_dotenv()

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

router = APIRouter()

AVAILABLE_MODELS_DETAIL: List[Dict[str, str]] = [
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
    {"id": "gemma-3-27b-it", "name": "Gemma 3 (37B)"},
    {"id": "gemma-3n-e4b-it", "name": "Gemma 3N (E4B)"},
]
AVAILABLE_MODELS = [model["id"] for model in AVAILABLE_MODELS_DETAIL]

class ChatRequest(BaseModel):
    message: str
    model: str

class ChatResponse(BaseModel):
    reply: str

class Model(BaseModel):
    id: str
    name: str

@router.get("/models", response_model=List[Model])
async def get_models():
    """
    利用可能なモデルのリストを返します。
    """
    return AVAILABLE_MODELS_DETAIL

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ユーザーからのメッセージを受け取り、応答を生成します。
    """
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
        
    try:
        model = ChatGoogleGenerativeAI(
            model=request.model,
            temperature=0.0,
        )
        prompt = client.pull_prompt("test2")
        messages = prompt.format_messages()
        messages.append(("human", request.message))
        response = model.invoke(messages)
        return ChatResponse(reply=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 