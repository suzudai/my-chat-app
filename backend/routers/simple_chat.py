import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models import AVAILABLE_MODELS, is_valid_model, get_available_models, get_available_embedding_models, get_model_client, get_model_provider, Model

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
    ユーザーからのメッセージを受け取り、指定されたモデルを使用して応答を生成します。
    """
    if not is_valid_model(request.model):
        raise HTTPException(status_code=400, detail="無効なモデルが指定されました。")
    
    try:
        provider = get_model_provider(request.model)
        
        if provider == "google":
            # Google Generative AI クライアントを使用
            model = get_model_client(request.model)
            prompt = f"""
            以下のガイドラインに従って、ユーザーとの会話を行ってください。
            ---
            ## あなたの役割

            あなたはフレンドリーかつプロフェッショナルな **AIチャットアシスタント** です。  
            ユーザーの質問に対して、**正確かつ分かりやすく**、**簡潔に**回答してください。
            ---
            ## 回答スタイル

            - 口調は **丁寧だが親しみやすく**
            - 誤解を防ぐために、**簡単な言葉で説明**
            - 必要に応じて **Markdown形式（箇条書き・コードブロックなど）** を使用
            ---
            ## 回答時のポイント

            - **質問の意図を汲み取って**、的確な内容を返答
            - 不明確な場合は、**丁寧に質問し直す**
            - 回答には、以下の形式を使う：
            - 見出し（`#`）
            - 改行は2回行う (`\n\n`)
            - 箇条書き（`-`）
            - 番号付きリスト（`1.`, `2.`）
            - 区切り線（`---`）
            - コードブロック（例は下記）
            ---
            ## コード出力の例
            ```python
            def greet(name):
                return f"Hello, {{name}}!"
            ```
            
            # ユーザーの質問
            {request.message}
            """
            response = model.generate_content(prompt)
            return ChatResponse(reply=response.text)
            
        elif provider == "azure":
            # Azure OpenAI クライアントを使用
            client = get_model_client(request.model)
            response = client.chat.completions.create(
                model=request.model,  # デプロイメント名
                messages=[
                    {
                        "role": "system",
                        "content": """あなたはフレンドリーかつプロフェッショナルなAIチャットアシスタントです。
                        ユーザーの質問に対して、正確かつ分かりやすく、簡潔に回答してください。
                        必要に応じてMarkdown形式を使用してください。"""
                    },
                    {
                        "role": "user",
                        "content": request.message
                    }
                ],
                temperature=0.0
            )
            return ChatResponse(reply=response.choices[0].message.content)
        else:
            raise HTTPException(status_code=400, detail=f"サポートされていないプロバイダー: {provider}")
        
    except Exception as e:
        # エラーログを記録することが望ましい
        raise HTTPException(status_code=500, detail=str(e)) 