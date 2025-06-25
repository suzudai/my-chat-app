import React, { useState } from 'react';
import { DocumentInfo, ApiResponse } from '../types';
import FileUpload from './FileUpload';

// SVG アイコンコンポーネント
const PlusIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);

const TrashIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
  </svg>
);

const DocumentIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
  </svg>
);

interface DocumentListProps {
  documents: DocumentInfo[];
  selectedDocument: string | null;
  onDocumentSelect: (document: DocumentInfo | null) => void;
  onDocumentsChange: () => void;
  isLoading: boolean;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocument,
  onDocumentSelect,
  onDocumentsChange,
  isLoading
}) => {
  const [showUpload, setShowUpload] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleDeleteClick = (document: DocumentInfo, e: React.MouseEvent) => {
    e.stopPropagation();
    if (deleteConfirm === document.source_path) {
      handleDeleteDocument(document);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(document.source_path);
      // 3秒後に確認状態をリセット
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const handleDeleteDocument = async (document: DocumentInfo) => {
    try {
      const response = await fetch('/api/langchainchatrag/documents', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_path: document.source_path }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '削除に失敗しました');
      }

      const result: ApiResponse = await response.json();
      
      if (result.success) {
        // 削除されたドキュメントが選択中だった場合は選択を解除
        if (selectedDocument === document.source_path) {
          onDocumentSelect(null);
        }
        onDocumentsChange();
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert(error instanceof Error ? error.message : '削除エラーが発生しました');
    }
  };

  const handleUploadSuccess = () => {
    setShowUpload(false);
    onDocumentsChange();
  };

  const handleUploadError = (error: string) => {
    alert(error);
  };

  const getFileIcon = (fileType: string): string => {
    switch (fileType.toLowerCase()) {
      case '.pdf':
        return '📄';
      case '.docx':
      case '.doc':
        return '📝';
      case '.pptx':
      case '.ppt':
        return '📊';
      default:
        return '📄';
    }
  };

  const truncateFileName = (fileName: string, maxLength: number = 25) => {
    return fileName.length > maxLength ? fileName.substring(0, maxLength) + '...' : fileName;
  };

  return (
    <div className="h-full flex flex-col">
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-100 flex items-center">
            <DocumentIcon className="w-5 h-5 mr-2" />
            ドキュメント一覧
          </h2>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="p-2 bg-teal-600 hover:bg-teal-700 rounded-lg transition-colors duration-200 flex items-center justify-center"
            title="ドキュメントを追加"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>

        {/* ファイルアップロード */}
        {showUpload && (
          <div className="mt-4">
            <FileUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
        )}
      </div>

      {/* ドキュメントリスト */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-400">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto"></div>
            <p className="mt-2">読み込み中...</p>
          </div>
        ) : (
          <div className="p-2">
            {/* 全体を対象にするオプション */}
            <div
              onClick={() => onDocumentSelect(null)}
              className={`p-3 mb-2 rounded-lg cursor-pointer transition-all duration-200 border ${
                selectedDocument === null
                  ? 'bg-teal-600 border-teal-500 shadow-lg'
                  : 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className={`font-medium text-sm leading-5 ${
                    selectedDocument === null ? 'text-white' : 'text-gray-200'
                  }`}>
                    📚 すべてのドキュメント
                  </h3>
                  <div className={`text-xs mt-1 ${
                    selectedDocument === null ? 'text-teal-100' : 'text-gray-400'
                  }`}>
                    全ドキュメントから検索
                  </div>
                </div>
              </div>
            </div>

            {/* ドキュメント一覧 */}
            {documents.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <DocumentIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>ドキュメントがありません</p>
                <p className="text-sm mt-1">ドキュメントを追加してください</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.source_path}
                    onClick={() => onDocumentSelect(doc)}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      selectedDocument === doc.source_path
                        ? 'bg-teal-600 border-teal-500 shadow-lg'
                        : 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className={`font-medium text-sm leading-5 ${
                          selectedDocument === doc.source_path ? 'text-white' : 'text-gray-200'
                        }`} title={doc.file_name}>
                          {getFileIcon(doc.file_type)} {truncateFileName(doc.file_name)}
                        </h3>
                        <div className={`text-xs mt-1 ${
                          selectedDocument === doc.source_path ? 'text-teal-100' : 'text-gray-400'
                        }`}>
                          {doc.file_type.toUpperCase()}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 ml-2">
                        <button
                          onClick={(e) => handleDeleteClick(doc, e)}
                          className={`p-1 rounded transition-colors duration-200 ${
                            deleteConfirm === doc.source_path
                              ? 'bg-red-600 hover:bg-red-700 text-white'
                              : 'text-gray-400 hover:text-red-400 hover:bg-gray-700'
                          }`}
                          title={deleteConfirm === doc.source_path ? 'クリックして削除' : '削除'}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* フッター情報 */}
      <div className="p-3 border-t border-gray-700 text-xs text-gray-500 text-center">
        {documents.length > 0 && `${documents.length}個のドキュメント`}
      </div>
    </div>
  );
};

export default DocumentList; 