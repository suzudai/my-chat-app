from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

router = APIRouter()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.0,
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ユーザーからのメッセージを受け取り、応答を生成します。
    """
    try:
    #     prompt = client.pull_prompt("test2")
    #     messages = prompt.format_messages()
    #     messages.append(("human", request.message))
    #     response = llm.invoke(messages)
        test = """
# 見出し1
## 見出し2
### 見出し3
---
- 箇条書き1
- 箇条書き2
1. 番号付きリスト1
2. 番号付きリスト2
---
```python
def greet():
    return f"Hello!"
```
"""
        return ChatResponse(reply=test)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 