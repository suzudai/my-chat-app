from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
import google.generativeai as genai
import openai
import os

class Model(BaseModel):
    id: str
    name: str
    provider: str = "google"  # "google" or "azure"

# 利用可能なチャットモデルの詳細定義
AVAILABLE_CHAT_MODELS_DETAIL: List[Dict[str, str]] = [
    # Google/Gemini モデル
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google"},
    {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash Experimental", "provider": "google"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite Preview", "provider": "google"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "google"},
    # {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "google"}, 利用不可
    {"id": "gemma-3n-e4b-it", "name": "Gemma 3n E4B", "provider": "google"},
    {"id": "gemma-3n-e2b-it", "name": "Gemma 3n E2B", "provider": "google"},


    
    # Gemma モデル（正しいモデルID）
    # {"id": "gemma-3n-e4b-it", "name": "Gemma 3n E4B", "provider": "google"},
    # {"id": "gemma-3-27b-i", "name": "Gemma 3 27B", "provider": "google"},
    
    # # Azure OpenAI モデル
    # {"id": "gpt-4o", "name": "GPT-4o", "provider": "azure"},
    # {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "azure"},
    # {"id": "gpt-4", "name": "GPT-4", "provider": "azure"},
    # {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo", "provider": "azure"},
]

# 利用可能なエンベディングモデルの詳細定義
AVAILABLE_EMBEDDING_MODELS_DETAIL: List[Dict[str, str]] = [
    # Google エンベディングモデル
    {"id": "embedding-gemini", "name": "Gemini Embedding", "provider": "google", "model_name": "models/embedding-001"},
    {"id": "embedding-gemini-text", "name": "Gemini Text Embedding", "provider": "google", "model_name": "models/text-embedding-004"},
    
    # # Azure OpenAI エンベディングモデル
    # {"id": "embedding-ada-002", "name": "Text Embedding Ada 002", "provider": "azure", "model_name": "text-embedding-ada-002"},
    # {"id": "embedding-3-small", "name": "Text Embedding 3 Small", "provider": "azure", "model_name": "text-embedding-3-small"},
    # {"id": "embedding-3-large", "name": "Text Embedding 3 Large", "provider": "azure", "model_name": "text-embedding-3-large"},
]

# チャットモデルIDのリスト
AVAILABLE_MODELS = [model["id"] for model in AVAILABLE_CHAT_MODELS_DETAIL]

# エンベディングモデルIDのリスト
AVAILABLE_EMBEDDING_MODELS = [model["id"] for model in AVAILABLE_EMBEDDING_MODELS_DETAIL]

def get_available_models() -> List[Model]:
    """利用可能なチャットモデルのリストを返します"""
    return [Model(**model) for model in AVAILABLE_CHAT_MODELS_DETAIL]

def get_available_embedding_models() -> List[Model]:
    """利用可能なエンベディングモデルのリストを返します"""
    return [Model(**{k: v for k, v in model.items() if k != "model_name"}) for model in AVAILABLE_EMBEDDING_MODELS_DETAIL]

def is_valid_model(model_id: str) -> bool:
    """指定されたモデルIDが有効かどうかを確認します"""
    return model_id in AVAILABLE_MODELS

def is_valid_embedding_model(model_id: str) -> bool:
    """指定されたエンベディングモデルIDが有効かどうかを確認します"""
    return model_id in AVAILABLE_EMBEDDING_MODELS

def get_model_provider(model_id: str) -> str:
    """チャットモデルIDからプロバイダーを取得"""
    for model in AVAILABLE_CHAT_MODELS_DETAIL:
        if model["id"] == model_id:
            return model["provider"]
    raise ValueError(f"無効なモデルID: {model_id}")

def get_embedding_model_info(model_id: str) -> Dict[str, str]:
    """エンベディングモデルIDから詳細情報を取得"""
    for model in AVAILABLE_EMBEDDING_MODELS_DETAIL:
        if model["id"] == model_id:
            return model
    raise ValueError(f"無効なエンベディングモデルID: {model_id}")

# モデルインスタンスのキャッシュ
_model_cache: Dict[str, Union[ChatGoogleGenerativeAI, AzureChatOpenAI]] = {}
_embeddings_cache: Dict[str, Union[GoogleGenerativeAIEmbeddings, AzureOpenAIEmbeddings]] = {}
_client_cache: Dict[str, Union[genai.GenerativeModel, openai.AzureOpenAI]] = {}

def get_model_instance(model_id: str, temperature: float = 0.0) -> Union[ChatGoogleGenerativeAI, AzureChatOpenAI]:
    """
    モデルIDからLangChainのチャットモデルインスタンスを取得（キャッシュ付き）
    
    Args:
        model_id: モデルID (例: "gemini-2.5-pro", "gpt-4o")
        temperature: 温度パラメータ (0.0-1.0)
    
    Returns:
        Union[ChatGoogleGenerativeAI, AzureChatOpenAI]: LangChainのチャットモデルインスタンス
    """
    if not is_valid_model(model_id):
        raise ValueError(f"無効なモデルID: {model_id}. 利用可能なモデル: {AVAILABLE_MODELS}")
    
    cache_key = f"{model_id}_{temperature}"
    
    if cache_key not in _model_cache:
        provider = get_model_provider(model_id)
        
        if provider == "google":
            _model_cache[cache_key] = ChatGoogleGenerativeAI(
                model=model_id,
                temperature=temperature,
            )
        elif provider == "azure":
            # Azure OpenAI の設定
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if not azure_endpoint or not api_key:
                raise ValueError("Azure OpenAI の環境変数が設定されていません: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")
            
            _model_cache[cache_key] = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                azure_deployment=model_id,  # デプロイメント名
                temperature=temperature,
            )
        else:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
    
    return _model_cache[cache_key]

def get_model_client(model_id: str, **kwargs) -> Union[genai.GenerativeModel, openai.AzureOpenAI]:
    """
    モデル名だけを引数で渡してクライアントを返却
    
    Args:
        model_id: モデルID (例: "gemini-2.5-pro", "gpt-4o")
        **kwargs: 追加の設定パラメータ
    
    Returns:
        Union[genai.GenerativeModel, openai.AzureOpenAI]: ネイティブクライアント
    """
    if not is_valid_model(model_id):
        raise ValueError(f"無効なモデルID: {model_id}. 利用可能なモデル: {AVAILABLE_MODELS}")
    
    cache_key = f"client_{model_id}_{hash(str(sorted(kwargs.items())))}"
    
    if cache_key not in _client_cache:
        provider = get_model_provider(model_id)
        
        if provider == "google":
            # Google Generative AI クライアント
            _client_cache[cache_key] = genai.GenerativeModel(
                model_name=model_id,
                **kwargs
            )
        elif provider == "azure":
            # Azure OpenAI クライアント
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if not azure_endpoint or not api_key:
                raise ValueError("Azure OpenAI の環境変数が設定されていません: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")
            
            _client_cache[cache_key] = openai.AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                **kwargs
            )
        else:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
    
    return _client_cache[cache_key]

def get_embeddings_model(embedding_model_id: str = "embedding-gemini") -> Union[GoogleGenerativeAIEmbeddings, AzureOpenAIEmbeddings]:
    """
    エンベディングモデルIDからエンベディングモデルインスタンスを取得（キャッシュ付き）
    
    Args:
        embedding_model_id: エンベディングモデルID (例: "embedding-gemini", "embedding-ada-002")
    
    Returns:
        Union[GoogleGenerativeAIEmbeddings, AzureOpenAIEmbeddings]: エンベディングモデルインスタンス
    """
    if not is_valid_embedding_model(embedding_model_id):
        raise ValueError(f"無効なエンベディングモデルID: {embedding_model_id}. 利用可能なモデル: {AVAILABLE_EMBEDDING_MODELS}")
    
    if embedding_model_id not in _embeddings_cache:
        model_info = get_embedding_model_info(embedding_model_id)
        provider = model_info["provider"]
        model_name = model_info["model_name"]
        
        if provider == "google":
            _embeddings_cache[embedding_model_id] = GoogleGenerativeAIEmbeddings(model=model_name)
        elif provider == "azure":
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if not azure_endpoint or not api_key:
                raise ValueError("Azure OpenAI の環境変数が設定されていません: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")
            
            _embeddings_cache[embedding_model_id] = AzureOpenAIEmbeddings(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                azure_deployment=model_name,
            )
        else:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
    
    return _embeddings_cache[embedding_model_id]

# デフォルトモデル設定（Gemini 1.5 Flash のクォータ制限を回避）
DEFAULT_CHAT_MODEL_ID = "gemini-2.0-flash-exp"  # 新しいデフォルトモデル
DEFAULT_EMBEDDING_MODEL_ID = "embedding-gemini"