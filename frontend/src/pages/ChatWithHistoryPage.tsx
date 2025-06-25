import React, { useState, useCallback, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  ChatMessage, 
  ChatHistorySession, 
  ChatResponse, 
  BackendChatMessage, 
  BackendChatSession,
  CreateSessionResponse 
} from '../../types';
import ChatDisplay from '../../components/ChatDisplay';
import MessageInput from '../../components/MessageInput';
import ErrorMessage from '../../components/ErrorMessage';
import ChatHistoryList from '../../components/ChatHistoryList';
import { OutletContextProps } from '../../src/Layout';

const ChatWithHistoryPage: React.FC = () => {
  const { selectedModelId, isLoading, setIsLoading } = useOutletContext<OutletContextProps>();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatHistorySession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState<boolean>(true);

  // チャット履歴セッション一覧を取得
  const fetchSessions = useCallback(async () => {
    try {
      setSessionsLoading(true);
      const response = await fetch('/api/langchain/chat-sessions');
      if (!response.ok) {
        throw new Error('Failed to fetch chat sessions');
      }
      const data: BackendChatSession[] = await response.json();
      
      // バックエンドデータをフロントエンド形式に変換
      const sessionsWithDates = data.map(session => ({
        thread_id: session.thread_id,
        title: session.title,
        created_at: new Date(session.updated_at),
        last_message_at: new Date(session.last_message_at || session.updated_at),
        updated_at: session.updated_at,
        message_count: session.message_count || 0
      }));
      
      setSessions(sessionsWithDates);
    } catch (e) {
      console.error('セッション取得エラー:', e);
      setError('チャット履歴の取得に失敗しました');
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  // 特定セッションのメッセージを取得
  const fetchSessionMessages = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/langchain/chat-sessions/${sessionId}/messages`);
      if (!response.ok) {
        throw new Error('Failed to fetch session messages');
      }
      const data: BackendChatMessage[] = await response.json();
      
      // バックエンドデータをフロントエンド形式に変換
      const messagesWithDates = data.map((msg, index) => ({
        id: `${msg.role}-${index}-${Date.now()}`,
        text: msg.content,
        sender: msg.role === 'user' ? 'user' as const : 'ai' as const,
        timestamp: new Date(msg.timestamp),
        role: msg.role,
        content: msg.content
      }));
      
      setMessages(messagesWithDates);
    } catch (e) {
      console.error('メッセージ取得エラー:', e);
      setError('メッセージの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [setIsLoading]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // セッション選択時の処理
  const handleSessionSelect = useCallback((session: ChatHistorySession | null) => {
    if (session) {
      setSelectedSessionId(session.thread_id);
      fetchSessionMessages(session.thread_id);
    } else {
      setSelectedSessionId(null);
      setMessages([]);
    }
    setError(null);
  }, [fetchSessionMessages]);

  // 新規セッション作成
  const handleNewSession = useCallback(async () => {
    try {
      const response = await fetch('/api/langchain/chat-sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create new session');
      }

      const newSession: CreateSessionResponse = await response.json();
      const sessionWithDates: ChatHistorySession = {
        thread_id: newSession.thread_id,
        title: newSession.title,
        created_at: new Date(),
        last_message_at: new Date(),
        message_count: 0
      };

      setSessions(prev => [sessionWithDates, ...prev]);
      setSelectedSessionId(sessionWithDates.thread_id);
      setMessages([]);
      setError(null);
    } catch (e) {
      console.error('新規セッション作成エラー:', e);
      setError('新しいチャットの作成に失敗しました');
    }
  }, []);

  // セッション削除
  const handleDeleteSession = useCallback(async (sessionId: string) => {
    try {
      const response = await fetch(`/api/langchain/chat-sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      setSessions(prev => prev.filter(session => session.thread_id !== sessionId));
      
      if (selectedSessionId === sessionId) {
        setSelectedSessionId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error('セッション削除エラー:', e);
      setError('チャットの削除に失敗しました');
    }
  }, [selectedSessionId]);

  // タイトル更新
  const handleTitleUpdate = useCallback(async (sessionId: string, newTitle: string) => {
    try {
      const response = await fetch(`/api/langchain/chat-sessions/${sessionId}/title`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle }),
      });

      if (!response.ok) {
        throw new Error('Failed to update title');
      }

      // セッション一覧でタイトルを更新
      setSessions(prev => prev.map(session => 
        session.thread_id === sessionId
          ? { ...session, title: newTitle }
          : session
      ));
    } catch (e) {
      console.error('タイトル更新エラー:', e);
      throw new Error('タイトルの更新に失敗しました');
    }
  }, []);

  const handleSendMessage = useCallback(async (userInput: string) => {
    // 現在のセッションがない場合は新規作成
    let currentSessionId = selectedSessionId;
    if (!currentSessionId) {
      try {
        const response = await fetch('/api/langchain/chat-sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to create new session');
        }

        const newSession: CreateSessionResponse = await response.json();
        const sessionWithDates: ChatHistorySession = {
          thread_id: newSession.thread_id,
          title: newSession.title,
          created_at: new Date(),
          last_message_at: new Date(),
          message_count: 0
        };

        setSessions(prev => [sessionWithDates, ...prev]);
        setSelectedSessionId(sessionWithDates.thread_id);
        currentSessionId = sessionWithDates.thread_id;
      } catch (e) {
        console.error('新規セッション作成エラー:', e);
        setError('新しいチャットの作成に失敗しました');
        return;
      }
    }

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
      const response = await fetch('/api/langchain/chat-with-history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: userInput, 
          thread_id: currentSessionId,
          model_id: selectedModelId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response from AI');
      }

      const data: ChatResponse = await response.json();

      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}-${Math.random()}`,
        text: data.reply,
        sender: 'ai',
        timestamp: new Date(),
        sources: data.sources
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);

      // メッセージ送信後にセッションリストを更新して、最終メッセージ日時を反映
      fetchSessions();

    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedSessionId, setIsLoading, selectedModelId, fetchSessions]);

  const selectedSession = sessions.find(session => session.thread_id === selectedSessionId);

  return (
    <div className="flex h-full overflow-hidden">
      {/* 左側のチャット履歴一覧 */}
      <div className="w-80 flex-shrink-0 p-4 border-r border-gray-700 overflow-y-auto">
        <ChatHistoryList
          sessions={sessions}
          selectedSessionId={selectedSessionId}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          onTitleUpdate={handleTitleUpdate}
          isLoading={sessionsLoading}
        />
      </div>

      {/* 右側のチャット部分 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 選択中のセッション表示 */}
        {selectedSession && (
          <div className="bg-blue-900 p-3 border-b border-gray-700">
            <div className="text-sm text-blue-200">
              選択中のチャット: <span className="font-medium">{selectedSession.title}</span>
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
            placeholder={selectedSession 
              ? `${selectedSession.title} で会話を続ける...`
              : "新しいチャットを開始してください..."
            }
          />
        </div>
      </div>
    </div>
  );
};

export default ChatWithHistoryPage; 