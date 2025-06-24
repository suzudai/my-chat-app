import os
import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from models import get_embeddings_model, get_model_instance, DEFAULT_CHAT_MODEL_ID
from langchain_core.documents import Document

load_dotenv()

def delete_vector_store():
    # 既にベクトルストアがあれば削除
    if os.path.exists("/code/my-chat-app/backend/langchain_rag/chroma_db"):
        shutil.rmtree("/code/my-chat-app/backend/langchain_rag/chroma_db")

def load_or_create_vector_store(embedding_model_id="embedding-gemini"):
    # ベクトルストアを読み込むor新規作成
    embeddings = get_embeddings_model(embedding_model_id)
    vector_store = Chroma(collection_name="my_collection", embedding_function=embeddings, persist_directory=f"/code/my-chat-app/backend/langchain_rag/chroma_db")
    return vector_store

def get_document_loader(doc_path):
    """
    ファイル拡張子に基づいて適切なローダーを返す
    """
    file_extension = Path(doc_path).suffix.lower()
    
    if file_extension == '.pdf':
        return PyPDFLoader(doc_path)
    elif file_extension in ['.docx', '.doc']:
        return Docx2txtLoader(doc_path)
    elif file_extension in ['.pptx', '.ppt']:
        return UnstructuredPowerPointLoader(doc_path)
    else:
        raise ValueError(f"サポートされていないファイル形式です: {file_extension}. PDF(.pdf), Word(.docx, .doc), PowerPoint(.pptx, .ppt)のみサポートされています。")

def get_documents_list():
    """
    ベクトルストアに保存されているドキュメントの一覧を取得する
    """
    try:
        vector_store = load_or_create_vector_store()
        collection = vector_store._collection
        results = collection.get()
        
        # ユニークなドキュメントを取得
        unique_documents = {}
        for metadata in results["metadatas"]:
            if metadata and "source_path" in metadata:
                source_path = metadata["source_path"]
                if source_path not in unique_documents:
                    file_name = Path(source_path).name
                    file_type = Path(source_path).suffix.upper()
                    unique_documents[source_path] = {
                        "file_name": file_name,
                        "file_type": file_type,
                        "source_path": source_path
                    }
        
        return list(unique_documents.values())
    except Exception as e:
        print(f"ドキュメント一覧取得エラー: {e}")
        return []

def delete_document_from_vector_store(source_path):
    """
    ベクトルストアから特定のドキュメントを削除し、物理ファイルも削除する
    """
    try:
        vector_store = load_or_create_vector_store()
        collection = vector_store._collection
        
        # source_pathまたはファイル名で検索を試行
        results = collection.get(where={"source_path": source_path})
        
        # source_pathで見つからない場合はfile_nameで検索
        if not results["ids"]:
            file_name = Path(source_path).name
            results = collection.get(where={"file_name": source_path})
            
        if not results["ids"]:
            return f"ドキュメントが見つかりません: {Path(source_path).name}"
        
        # ベクトルストアからドキュメントを削除
        collection.delete(ids=results["ids"])
        
        # 物理ファイルの削除を試行
        file_deleted = False
        file_path = Path(source_path)
        if file_path.exists():
            try:
                file_path.unlink()  # ファイルを削除
                file_deleted = True
            except Exception as file_error:
                print(f"物理ファイル削除エラー: {file_error}")
        
        file_name = Path(source_path).name
        chunk_count = len(results['ids'])
        
        if file_deleted:
            return f"✅ ドキュメント '{file_name}' をベクトルストアと物理ファイルから削除しました。({chunk_count}個のチャンクを削除)"
        else:
            return f"✅ ドキュメント '{file_name}' をベクトルストアから削除しました。({chunk_count}個のチャンクを削除)\n⚠️ 物理ファイルは見つからないか削除できませんでした。"
        
    except Exception as e:
        return f"エラー: ドキュメントの削除中にエラーが発生しました: {str(e)}"

def save_uploaded_file(file_content, filename, upload_dir="/code/my-chat-app/backend/langchain_rag/files"):
    """
    アップロードされたファイルを保存する
    """
    try:
        # アップロードディレクトリが存在しない場合は作成
        os.makedirs(upload_dir, exist_ok=True)
        
        # ファイルパスを作成
        file_path = os.path.join(upload_dir, filename)
        
        # ファイルが既に存在する場合は、ユニークな名前を生成
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(file_path):
            new_filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(upload_dir, new_filename)
            counter += 1
        
        # ファイルを保存
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
        
    except Exception as e:
        raise Exception(f"ファイル保存エラー: {str(e)}")

def add_document(vector_store, doc_path):
    """
    ドキュメントをベクトルストアに追加する
    サポート形式: PDF, Word (docx, doc), PowerPoint (pptx, ppt)
    """
    # ファイルの存在確認
    if not os.path.exists(doc_path):
        return f"エラー: ファイルが見つかりません: {doc_path}"
    
    try:
        collection = vector_store._collection  # 内部の ChromaDB コレクションにアクセス
        results = collection.get()  # 全ドキュメント取得
        
        for metadata in results["metadatas"]:
            if metadata and metadata.get("source_path") == str(doc_path):
                return f"ドキュメントはすでに追加されています: {Path(doc_path).name}"
        
        # ファイル形式に応じたローダーを取得
        loader = get_document_loader(doc_path)
        
        # ドキュメントを分割する
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(loader.load())
        
        # ドキュメントが空でないことを確認
        if not docs:
            return f"エラー: ドキュメントからテキストを抽出できませんでした: {doc_path}"
        
        # メタデータを追加
        for doc in docs:
            doc.metadata["file_name"] = doc_path
            doc.metadata["file_type"] = Path(doc_path).suffix.upper()
            doc.metadata["source_path"] = str(doc_path)
            
        # ドキュメントをベクトルストアに追加
        vector_store.add_documents(docs)
        file_name = Path(doc_path).name
        file_type = Path(doc_path).suffix.upper()

        return f"✅ {file_type}ファイル '{file_name}' を正常に追加しました。({len(docs)}個のチャンクに分割)"
        
    except Exception as e:
        return f"エラー: ドキュメントの追加中にエラーが発生しました: {str(e)}"

def upload_and_add_document(file_content, filename):
    """
    ファイルをアップロードしてベクトルストアに追加する
    """
    try:
        # ファイルを保存
        file_path = save_uploaded_file(file_content, filename)
        
        # ベクトルストアに追加
        vector_store = load_or_create_vector_store()
        result = add_document(vector_store, file_path)
        
        return result
        
    except Exception as e:
        return f"エラー: アップロード処理中にエラーが発生しました: {str(e)}"

def vector_search_flow(vector_store, query, document_filter=None, model_name=DEFAULT_CHAT_MODEL_ID):
    """
    ベクトル検索を実行する
    document_filter: 特定のドキュメントに絞り込む場合のフィルター
    model_name: 使用するモデル名
    """
    # 後でベクトルストアを検索するためにretrieverを作成
    if document_filter:
        # 特定のドキュメントに絞り込む
        retriever = vector_store.as_retriever(
            search_kwargs={"filter": {"source_path": document_filter}}
        )
    else:
        retriever = vector_store.as_retriever()

    # 共通のモデル管理からインスタンスを取得
    model = get_model_instance(model_name)

    # チェーンを作成
    qa_chain = RetrievalQA.from_chain_type(llm=model, retriever=retriever)

    # チェーンを実行
    answer = qa_chain.invoke(query)
    return answer

def get_supported_formats():
    """
    サポートされているファイル形式のリストを返す
    """
    return {
        "PDF": [".pdf"],
        "Word": [".docx", ".doc"],
        "PowerPoint": [".pptx", ".ppt"]
    }

def get_rag_flow(query, selected_document=None, model_name=DEFAULT_CHAT_MODEL_ID, embedding_model_id="embedding-gemini"):
    """
    RAG機能のメインフロー
    selected_document: 特定のドキュメントに絞り込む場合のsource_path
    model_name: 使用するモデル名
    embedding_model_id: エンベディングモデルID (例: "embedding-gemini", "embedding-ada-002")
    """
    vector_store = load_or_create_vector_store(embedding_model_id)
    answer = vector_search_flow(vector_store, query, selected_document, model_name)
    return answer["result"]

if __name__ == "__main__":
    # ベクトルストアを作成
    vector_store = load_or_create_vector_store()
    
    result = add_document(vector_store, "./backend/langchain_rag/files/NIPS-2017-attention-is-all-you-need-Paper.pdf")

    # delete_vector_store()