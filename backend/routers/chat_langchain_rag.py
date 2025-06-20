from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from langchains.langchain_rag import get_rag_flow, get_documents_list, upload_and_add_document, delete_document_from_vector_store

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str
    selected_document: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str

class DocumentInfo(BaseModel):
    file_name: str
    file_type: str
    source_path: str

class DeleteDocumentRequest(BaseModel):
    source_path: str

class ApiResponse(BaseModel):
    success: bool
    message: str

class Model(BaseModel):
    id: str
    name: str

@router.get("/documents", response_model=List[DocumentInfo])
async def get_documents():
    """
    ベクトルストアに保存されているドキュメントの一覧を取得します。
    """
    documents = get_documents_list()
    return documents

@router.post("/upload", response_model=ApiResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    ドキュメントをアップロードしてベクトルストアに追加します。
    """
    # ファイル形式の検証
    allowed_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.ppt']
    file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
        )
    
    try:
        # ファイル内容を読み取り
        file_content = await file.read()
        
        # ファイルサイズ制限（10MB）
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="ファイルサイズが大きすぎます（最大10MB）")
        
        # アップロードとベクトルストアへの追加
        result = upload_and_add_document(file_content, file.filename)
        
        if result.startswith("✅"):
            return ApiResponse(success=True, message=result)
        else:
            return ApiResponse(success=False, message=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents", response_model=ApiResponse)
async def delete_document(request: DeleteDocumentRequest):
    """
    ベクトルストアからドキュメントを削除します。
    """
    try:
        result = delete_document_from_vector_store(request.source_path)
        
        if result.startswith("✅"):
            return ApiResponse(success=True, message=result)
        else:
            return ApiResponse(success=False, message=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/langchain-rag-chat")
async def langchain_rag(request: ChatRequest):
    answer = get_rag_flow(request.message, request.selected_document)
    return ChatResponse(reply=answer)