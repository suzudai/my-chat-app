from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.0,
)

@router.get("/langchain_chat")
async def get_data():


    messages = [
        (
            "system",
            "You are a helpful assistant that translates English to French. Translate the user sentence.",
        ),
        ("human", "I love programming."),
    ]
    response = llm.invoke(messages)
    print(response.content)

    return {"message": response.content} 


@router.get("/langchain_chat2")
async def chainwithsmith():
    client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

    # Promptを取得
    prompt = client.pull_prompt("test2")

    messages = prompt.format_messages()

    # チェーンを実行
    response = llm.invoke(messages)
    print(response.content)

    return {"message": response.content} 