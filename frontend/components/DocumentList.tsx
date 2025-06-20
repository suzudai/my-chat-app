import React, { useState } from 'react';
import { DocumentInfo, ApiResponse } from '../types';
import FileUpload from './FileUpload';

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
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDeleteDocument = async (document: DocumentInfo) => {
    if (deleting) return;
    
    if (!confirm(`「${document.file_name}」を削除しますか？この操作は取り消せません。`)) {
      return;
    }

    setDeleting(document.source_path);

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
    } finally {
      setDeleting(null);
    }
  };

  const handleUploadSuccess = () => {
    setShowUpload(false);
    onDocumentsChange();
  };

  const handleUploadError = (error: string) => {
    alert(error);
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-teal-300 mb-4">ドキュメント一覧</h3>
        <div className="text-gray-400">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-teal-300">ドキュメント一覧</h3>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors"
        >
          {showUpload ? '閉じる' : '追加'}
        </button>
      </div>

      {/* ファイルアップロード */}
      {showUpload && (
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      )}
      
      {/* 全体を対象にするオプション */}
      <div
        className={`p-3 mb-2 rounded-lg cursor-pointer transition-colors ${
          selectedDocument === null
            ? 'bg-blue-600 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
        onClick={() => onDocumentSelect(null)}
      >
        <div className="font-medium">📚 すべてのドキュメント</div>
        <div className="text-sm text-gray-400">全ドキュメントから検索</div>
      </div>

      {/* ドキュメント一覧 */}
      {documents.length === 0 ? (
        <div className="text-gray-400 text-sm">
          ドキュメントが見つかりません
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.source_path}
              className={`p-3 rounded-lg transition-colors ${
                selectedDocument === doc.source_path
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <div 
                className="cursor-pointer"
                onClick={() => onDocumentSelect(doc)}
              >
                <div className="font-medium truncate" title={doc.file_name}>
                  {getFileIcon(doc.file_type)} {doc.file_name}
                </div>
                <div className="text-sm text-gray-400">{doc.file_type}</div>
              </div>
              
              {/* 削除ボタン */}
              <div className="mt-2 pt-2 border-t border-gray-600">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteDocument(doc);
                  }}
                  disabled={deleting === doc.source_path}
                  className="px-2 py-1 bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white text-xs rounded transition-colors"
                >
                  {deleting === doc.source_path ? '削除中...' : '🗑️ 削除'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
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

export default DocumentList; 