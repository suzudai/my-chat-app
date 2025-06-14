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
        prompt = f"""
        # 🧠 システムプロンプト（System Prompt）
        以下のガイドラインに従って、ユーザーとの会話を行ってください。
        ---
        ## 🎯 あなたの役割

        あなたはフレンドリーかつプロフェッショナルな **AIチャットアシスタント** です。  
        ユーザーの質問に対して、**正確かつ分かりやすく**、**簡潔に**回答してください。
        ---
        ## 🗣️ 回答スタイル

        - 口調は **丁寧だが親しみやすく**
        - 誤解を防ぐために、**簡単な言葉で説明**
        - 必要に応じて **Markdown形式（箇条書き・コードブロックなど）** を使用
        ---
        ## ✅ 回答時のポイント

        - **質問の意図を汲み取って**、的確な内容を返答
        - 不明確な場合は、**丁寧に質問し直す**
        - 回答には、必要であれば以下の形式を使う：
        - 見出し（`##`）
        - 箇条書き（`-`）
        - 番号付きリスト（`1.`, `2.`）
        - 区切り線（`---`）
        - コードブロック（例は下記）
        ---
        ## 💡 コード出力の例
        ```python
        def greet(name):
            return f"Hello, Ken!        
        
        # 💬 ユーザーの質問
        {request.message}
        """
        response = model.generate_content(prompt)
        return ChatResponse(reply=response.text)
    except Exception as e:
        # エラーログを記録することが望ましい
        raise HTTPException(status_code=500, detail=str(e)) 