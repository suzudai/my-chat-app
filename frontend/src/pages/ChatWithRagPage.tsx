import React, { useState, useCallback, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ChatMessage, DocumentInfo } from '../../types';
import ChatDisplay from '../../components/ChatDisplay';
import MessageInput from '../../components/MessageInput';
import ErrorMessage from '../../components/ErrorMessage';
import DocumentList from '../../components/DocumentList';
import { OutletContextProps } from '../../src/Layout';

const ChatWithRagPage: React.FC = () => {
  const { selectedModelId, isLoading, setIsLoading } = useOutletContext<OutletContextProps>();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [documentsLoading, setDocumentsLoading] = useState<boolean>(true);

  // ドキュメント一覧を取得
  const fetchDocuments = useCallback(async () => {
    try {
      setDocumentsLoading(true);
      const response = await fetch('/api/langchainchatrag/documents');
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      const data: DocumentInfo[] = await response.json();
      setDocuments(data);
    } catch (e) {
      console.error('ドキュメント取得エラー:', e);
      setError('ドキュメント一覧の取得に失敗しました');
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDocumentSelect = useCallback((document: DocumentInfo | null) => {
    setSelectedDocument(document ? document.source_path : null);
  }, []);

  const handleDocumentsChange = useCallback(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleSendMessage = useCallback(async (userInput: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}-${Math.random()}`,
      text: userInput,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/langchainchatrag/langchain-rag-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: userInput, 
          model: selectedModelId,
          selected_document: selectedDocument
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response from AI');
      }

      const data = await response.json();

      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}-${Math.random()}`,
        text: data.reply,
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [setIsLoading, selectedModelId, selectedDocument]);

  const selectedDocumentInfo = documents.find(doc => doc.source_path === selectedDocument);

  return (
    <div className="flex h-full overflow-hidden">
      {/* 左側のドキュメント一覧 */}
      <div className="w-80 flex-shrink-0 p-4 border-r border-gray-700 overflow-y-auto">
        <DocumentList
          documents={documents}
          selectedDocument={selectedDocument}
          onDocumentSelect={handleDocumentSelect}
          onDocumentsChange={handleDocumentsChange}
          isLoading={documentsLoading}
        />
      </div>

      {/* 右側のチャット部分 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 選択中のドキュメント表示 */}
        {selectedDocumentInfo && (
          <div className="bg-blue-900 p-3 border-b border-gray-700">
            <div className="text-sm text-blue-200">
              選択中のドキュメント: <span className="font-medium">{selectedDocumentInfo.file_name}</span>
            </div>
          </div>
        )}

        <div className="flex-grow overflow-y-auto p-4">
          <ChatDisplay messages={messages} isLoading={isLoading} />
        </div>
        
        <div className="w-full md:w-2/3 mx-auto p-4">
          {error && (
            <div className="pb-2">
              <ErrorMessage message={error} />
            </div>
          )}
          <MessageInput 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading}
            placeholder={selectedDocumentInfo 
              ? `${selectedDocumentInfo.file_name} について質問してください...`
              : "すべてのドキュメントから検索して質問してください..."
            }
          />
        </div>
      </div>
    </div>
  );
};

export default ChatWithRagPage; 