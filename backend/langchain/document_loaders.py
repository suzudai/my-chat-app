import os
import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")


def delete_vector_store():
    # 既にベクトルストアがあれば削除
    if os.path.exists("/code/my-chat-app/backend/langchain/chroma_db"):
        shutil.rmtree("/code/my-chat-app/backend/langchain/chroma_db")

def load_or_create_vector_store():
    # ベクトルストアを読み込むor新規作成
    vector_store = Chroma(collection_name="my_collection", embedding_function=embeddings, persist_directory=f"/code/my-chat-app/backend/langchain/chroma_db")
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
            if metadata["source_path"] == str(doc_path):
                return f"ドキュメントはすでに追加されています: {doc_path}"
        
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

def vector_search_flow(vector_store, query):
    # 後でベクトルストアを検索するためにretrieverを作成
    retriever = vector_store.as_retriever()

    # モデルを作成
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

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

if __name__ == "__main__":
    # ベクトルストアを作成
    vector_store = load_or_create_vector_store()
    
    result = add_document(vector_store, "./backend/langchain/files/NIPS-2017-attention-is-all-you-need-Paper.pdf")
    print(result)

    # # 検索実行
    # answer = vector_search_flow(vector_store, "大学での研究について教えて")
    # print(f"\n検索結果:\n{answer}")

    # collection = vector_store._collection  # 内部の ChromaDB コレクションにアクセス
    # results = collection.get()  # 全ドキュメント取得
    # # 結果の表示
    # for doc_id, content, metadata in zip(results["ids"], results["documents"], results["metadatas"]):
    #     print(f"\n--- ID: {doc_id} ---")
    #     print(f"Metadata:\n{metadata}")

    # delete_vector_store()