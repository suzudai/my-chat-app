import React, { useState } from 'react';
import { ChatHistorySession } from '../types';

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

const ChatBubbleLeftRightIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
  </svg>
);

const EditIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
  </svg>
);

const CheckIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
  </svg>
);

const XMarkIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
  </svg>
);

interface ChatHistoryListProps {
  sessions: ChatHistorySession[];
  selectedSessionId: string | null;
  onSessionSelect: (session: ChatHistorySession | null) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onTitleUpdate: (sessionId: string, newTitle: string) => Promise<void>;
  isLoading: boolean;
}

const ChatHistoryList: React.FC<ChatHistoryListProps> = ({
  sessions,
  selectedSessionId,
  onSessionSelect,
  onNewSession,
  onDeleteSession,
  onTitleUpdate,
  isLoading
}) => {
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

  const handleDeleteClick = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (deleteConfirm === sessionId) {
      onDeleteSession(sessionId);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(sessionId);
      // 3秒後に確認状態をリセット
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const handleEditClick = (sessionId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(sessionId);
    setEditingTitle(currentTitle);
  };

  const handleTitleSave = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editingTitle.trim() === '') return;
    
    setIsUpdating(true);
    try {
      await onTitleUpdate(sessionId, editingTitle.trim());
      setEditingSessionId(null);
      setEditingTitle('');
    } catch (error) {
      console.error('タイトルの更新に失敗しました:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleTitleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleTitleInputKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleTitleSave(sessionId, e as any);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleTitleCancel(e as any);
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return '昨日';
    } else if (diffDays < 7) {
      return `${diffDays}日前`;
    } else {
      return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
    }
  };

  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  return (
    <div className="h-full flex flex-col">
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-100 flex items-center">
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            チャット履歴
          </h2>
          <button
            onClick={onNewSession}
            className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors duration-200 flex items-center justify-center"
            title="新しいチャット"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 履歴リスト */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-400">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2">読み込み中...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>チャット履歴がありません</p>
            <p className="text-sm mt-1">新しいチャットを開始してください</p>
          </div>
        ) : (
          <div className="p-2">
            {sessions.map((session) => (
              <div
                key={session.thread_id}
                onClick={() => onSessionSelect(session)}
                className={`p-3 mb-2 rounded-lg cursor-pointer transition-all duration-200 border ${
                  selectedSessionId === session.thread_id
                    ? 'bg-blue-600 border-blue-500 shadow-lg'
                    : 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {editingSessionId === session.thread_id ? (
                      <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => handleTitleInputKeyDown(e, session.thread_id)}
                          className="flex-1 bg-gray-700 text-white text-sm px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                          autoFocus
                          disabled={isUpdating}
                        />
                        <button
                          onClick={(e) => handleTitleSave(session.thread_id, e)}
                          disabled={isUpdating || editingTitle.trim() === ''}
                          className="p-1 text-green-400 hover:text-green-300 disabled:text-gray-500"
                          title="保存"
                        >
                          <CheckIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleTitleCancel}
                          disabled={isUpdating}
                          className="p-1 text-gray-400 hover:text-gray-300 disabled:text-gray-600"
                          title="キャンセル"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <h3 className={`font-medium text-sm leading-5 ${
                        selectedSessionId === session.thread_id ? 'text-white' : 'text-gray-200'
                      }`}>
                        {truncateTitle(session.title)}
                      </h3>
                    )}
                    <div className={`flex items-center mt-1 text-xs ${
                      selectedSessionId === session.thread_id ? 'text-blue-100' : 'text-gray-400'
                    }`}>
                      <span>{session.message_count || 0}件のメッセージ</span>
                      <span className="mx-1">•</span>
                      <span>{formatDate(session.last_message_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 ml-2">
                    {editingSessionId !== session.thread_id && (
                      <button
                        onClick={(e) => handleEditClick(session.thread_id, session.title, e)}
                        className="p-1 text-gray-400 hover:text-blue-400 hover:bg-gray-700 rounded transition-colors duration-200"
                        title="タイトルを編集"
                      >
                        <EditIcon className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDeleteClick(session.thread_id, e)}
                      className={`p-1 rounded transition-colors duration-200 ${
                        deleteConfirm === session.thread_id
                          ? 'bg-red-600 hover:bg-red-700 text-white'
                          : 'text-gray-400 hover:text-red-400 hover:bg-gray-700'
                      }`}
                      title={deleteConfirm === session.thread_id ? 'クリックして削除' : '削除'}
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

      {/* フッター情報 */}
      <div className="p-3 border-t border-gray-700 text-xs text-gray-500 text-center">
        {sessions.length > 0 && `${sessions.length}個のセッション`}
      </div>
    </div>
  );
};

export default ChatHistoryList; 