import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { OutletContextProps } from '../Layout';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AgentResponse {
  agent: string;
  agent_name: string;
  response: string;
  timestamp: string;
}

interface VotingResult {
  [voter: string]: {
    [candidate: string]: {
      score: number;
      reason: string;
    };
  };
}

interface ConversationData {
  user_message?: string;
  agent_responses?: AgentResponse[];
  voting_results?: VotingResult;
  final_response?: string;
  timestamp: string;
}

interface Session {
  thread_id: string;
  title: string;
  updated_at: string;
  message_count: number;
  last_message_at: string;
}

const VotingGraphPage: React.FC = () => {
  const { selectedModelId, isLoading, setIsLoading } = useOutletContext<OutletContextProps>();
  const [message, setMessage] = useState('');
  const [conversations, setConversations] = useState<ConversationData[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showSessions, setShowSessions] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [currentStreamingData, setCurrentStreamingData] = useState<ConversationData | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversations, currentStreamingData]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('/api/voting-graph/voting-graph-sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('セッション取得エラー:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch('/api/voting-graph/voting-graph-sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentSessionId(data.thread_id);
        setConversations([]);
        setCurrentStreamingData(null);
        fetchSessions();
      }
    } catch (error) {
      console.error('新規セッション作成エラー:', error);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/voting-graph/voting-graph-sessions/${sessionId}/messages`);
      
      if (response.ok) {
        const data = await response.json();
        // 従来のメッセージ形式を新しい会話形式に変換
        const convertedConversations: ConversationData[] = [];
        
        for (let i = 0; i < data.length; i += 2) {
          const userMsg = data[i];
          const assistantMsg = data[i + 1];
          
          if (userMsg && userMsg.role === 'user') {
            const conversation: ConversationData = {
              user_message: userMsg.content,
              timestamp: userMsg.timestamp,
            };
            
            if (assistantMsg && assistantMsg.role === 'assistant') {
              // アシスタントメッセージからエージェントの応答を解析（簡単な実装）
              conversation.final_response = assistantMsg.content;
            }
            
            convertedConversations.push(conversation);
          }
        }
        
        setConversations(convertedConversations);
        setCurrentSessionId(sessionId);
        setCurrentStreamingData(null);
      }
    } catch (error) {
      console.error('セッション読み込みエラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!confirm('このセッションを削除しますか？')) return;

    try {
      const response = await fetch(`/api/voting-graph/voting-graph-sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSessions(sessions.filter(s => s.thread_id !== sessionId));
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null);
          setConversations([]);
          setCurrentStreamingData(null);
        }
      }
    } catch (error) {
      console.error('セッション削除エラー:', error);
    }
  };

  const updateSessionTitle = async (sessionId: string, newTitle: string) => {
    try {
      const response = await fetch(`/api/voting-graph/voting-graph-sessions/${sessionId}/title`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle }),
      });

      if (response.ok) {
        setSessions(sessions.map(s => 
          s.thread_id === sessionId ? { ...s, title: newTitle } : s
        ));
        setIsEditingTitle(null);
        setEditTitle('');
      }
    } catch (error) {
      console.error('タイトル更新エラー:', error);
    }
  };

  const handleStreamingChat = async (messageContent: string) => {
    try {
      const endpoint = currentSessionId 
        ? `/api/voting-graph/voting-graph-sessions/${currentSessionId}/chat-stream`
        : '/api/voting-graph/voting-graph-chat-stream';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageContent,
          model: selectedModelId,
        }),
      });

      if (!response.ok) {
        throw new Error('ストリーミングリクエストに失敗しました');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('レスポンスの読み取りに失敗しました');
      }

      // 新しい会話データを初期化
      const newConversation: ConversationData = {
        user_message: messageContent,
        agent_responses: [],
        timestamp: new Date().toISOString(),
      };

      setCurrentStreamingData(newConversation);

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'start':
                  // 開始メッセージ
                  break;

                case 'phase_start':
                  // フェーズ開始メッセージ
                  break;

                case 'agent_response':
                  setCurrentStreamingData(prev => {
                    if (!prev) return prev;
                    
                    const updatedAgentResponses = [...(prev.agent_responses || [])];
                    const existingIndex = updatedAgentResponses.findIndex(r => r.agent === data.agent);
                    
                    const agentResponse: AgentResponse = {
                      agent: data.agent,
                      agent_name: data.agent_name,
                      response: data.response,
                      timestamp: new Date().toISOString(),
                    };

                    if (existingIndex >= 0) {
                      updatedAgentResponses[existingIndex] = agentResponse;
                    } else {
                      updatedAgentResponses.push(agentResponse);
                    }

                    return {
                      ...prev,
                      agent_responses: updatedAgentResponses,
                    };
                  });
                  break;

                case 'voting_results':
                  setCurrentStreamingData(prev => {
                    if (!prev) return prev;
                    return {
                      ...prev,
                      voting_results: data.voting_results,
                    };
                  });
                  break;

                case 'final_response':
                  setCurrentStreamingData(prev => {
                    if (!prev) return prev;
                    return {
                      ...prev,
                      final_response: data.response,
                    };
                  });
                  break;

                case 'complete':
                  // ストリーミング完了時に会話履歴に追加
                  setConversations(prev => [...prev, currentStreamingData!]);
                  setCurrentStreamingData(null);
                  
                  // セッションIDを設定
                  if (data.thread_id && !currentSessionId) {
                    setCurrentSessionId(data.thread_id);
                  }
                  
                  // セッション一覧を更新
                  if (data.updated_title) {
                    fetchSessions();
                  }
                  break;

                case 'title_updated':
                  fetchSessions();
                  break;

                case 'error':
                  throw new Error(data.message);

                case 'end':
                  return; // ストリーミング終了
              }
            } catch (parseError) {
              console.warn('JSON解析エラー:', parseError, line);
            }
          }
        }
      }
    } catch (error) {
      console.error('ストリーミングチャットエラー:', error);
      throw error;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    setMessage('');
    setIsLoading(true);

    try {
      await handleStreamingChat(message);
    } catch (error) {
      console.error('チャットエラー:', error);
      // エラー時の処理
      const errorConversation: ConversationData = {
        user_message: message,
        final_response: 'エラーが発生しました。もう一度お試しください。',
        timestamp: new Date().toISOString(),
      };
      setConversations(prev => [...prev, errorConversation]);
      setCurrentStreamingData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ja-JP');
  };

  const currentSession = sessions.find(s => s.thread_id === currentSessionId);

  const getAgentIcon = (agent: string) => {
    switch (agent) {
      case 'logical_agent':
        return '🧠';
      case 'empathetic_agent':
        return '❤️';
      case 'concise_agent':
        return '⚡';
      default:
        return '🤖';
    }
  };

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case 'logical_agent':
        return 'border-blue-500 bg-blue-50/10';
      case 'empathetic_agent':
        return 'border-green-500 bg-green-50/10';
      case 'concise_agent':
        return 'border-yellow-500 bg-yellow-50/10';
      default:
        return 'border-gray-500 bg-gray-50/10';
    }
  };

  const renderAgentResponse = (agentResponse: AgentResponse) => (
    <div
      key={agentResponse.agent}
      className={`p-4 rounded-lg border-2 ${getAgentColor(agentResponse.agent)} mb-3`}
    >
      <div className="flex items-center space-x-2 mb-3">
        <span className="text-2xl">{getAgentIcon(agentResponse.agent)}</span>
        <h3 className="font-semibold text-lg">{agentResponse.agent_name}</h3>
        <span className="text-xs text-gray-400">
          {formatTimestamp(agentResponse.timestamp)}
        </span>
      </div>
      <div className="prose prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const isInline = !className;
              return !isInline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus as any}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {agentResponse.response}
        </ReactMarkdown>
      </div>
    </div>
  );

  const renderVotingResults = (votingResults: VotingResult) => (
    <div className="p-4 rounded-lg border-2 border-purple-500 bg-purple-50/10 mb-3">
      <div className="flex items-center space-x-2 mb-3">
        <span className="text-2xl">🗳️</span>
        <h3 className="font-semibold text-lg">投票結果</h3>
      </div>
      <div className="space-y-3">
        {Object.entries(votingResults).map(([voter, votes]) => (
          <div key={voter} className="bg-gray-800/50 p-3 rounded">
            <h4 className="font-medium mb-2 text-purple-300">
              {voter === 'logical_agent' ? '🧠 論理的思考エージェント' :
               voter === 'empathetic_agent' ? '❤️ 共感重視エージェント' :
               voter === 'concise_agent' ? '⚡ 簡潔要約エージェント' : voter}の投票:
            </h4>
            <div className="space-y-1">
              {Object.entries(votes).map(([candidate, voteData]) => (
                <div key={candidate} className="text-sm">
                  <span className="font-medium">
                    {candidate === 'logical_agent' ? '🧠 論理的思考' :
                     candidate === 'empathetic_agent' ? '❤️ 共感重視' :
                     candidate === 'concise_agent' ? '⚡ 簡潔要約' : candidate}:
                  </span>
                  <span className="ml-2 text-yellow-400">{voteData.score}点</span>
                  <div className="text-gray-300 ml-4">{voteData.reason}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderFinalResponse = (finalResponse: string) => (
    <div className="p-4 rounded-lg border-2 border-gold-500 bg-gold-50/10 mb-3" style={{ borderColor: '#FFD700', backgroundColor: 'rgba(255, 215, 0, 0.1)' }}>
      <div className="flex items-center space-x-2 mb-3">
        <span className="text-2xl">🏆</span>
        <h3 className="font-semibold text-lg text-yellow-300">最終回答</h3>
      </div>
      <div className="prose prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const isInline = !className;
              return !isInline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus as any}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {finalResponse}
        </ReactMarkdown>
      </div>
    </div>
  );

  const renderConversation = (conversation: ConversationData, index: number) => (
    <div key={index} className="mb-8">
      {/* ユーザーメッセージ */}
      {conversation.user_message && (
        <div className="flex justify-end mb-4">
          <div className="max-w-3xl p-4 rounded-lg bg-blue-600 text-white">
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {conversation.user_message}
              </ReactMarkdown>
            </div>
            <div className="text-xs opacity-70 mt-2">
              {formatTimestamp(conversation.timestamp)}
            </div>
          </div>
        </div>
      )}

      {/* エージェント応答 */}
      {conversation.agent_responses && conversation.agent_responses.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-3 text-gray-300">🤖 エージェント応答</h3>
          {conversation.agent_responses.map(renderAgentResponse)}
        </div>
      )}

      {/* 投票結果 */}
      {conversation.voting_results && (
        <div className="mb-4">
          {renderVotingResults(conversation.voting_results)}
        </div>
      )}

      {/* 最終回答 */}
      {conversation.final_response && (
        <div className="mb-4">
          {renderFinalResponse(conversation.final_response)}
        </div>
      )}
    </div>
  );

  return (
    <div className="flex h-full bg-gray-900 text-gray-100">
      {/* サイドバー */}
      <div className={`${showSessions ? 'w-80' : 'w-0'} transition-all duration-300 bg-gray-800 border-r border-gray-700 overflow-hidden`}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-blue-400">投票チャット履歴</h2>
            <button
              onClick={createNewSession}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
            >
              新規作成
            </button>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {sessions.map((session) => (
              <div
                key={session.thread_id}
                className={`p-3 border rounded cursor-pointer transition-colors ${
                  currentSessionId === session.thread_id
                    ? 'bg-blue-600 border-blue-500'
                    : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  {isEditingTitle === session.thread_id ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => updateSessionTitle(session.thread_id, editTitle)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          updateSessionTitle(session.thread_id, editTitle);
                        }
                        if (e.key === 'Escape') {
                          setIsEditingTitle(null);
                          setEditTitle('');
                        }
                      }}
                      className="bg-transparent border-b border-blue-400 text-sm font-medium flex-1 mr-2 focus:outline-none"
                      autoFocus
                    />
                  ) : (
                    <h3
                      className="text-sm font-medium text-gray-100 truncate flex-1 mr-2"
                      onClick={() => loadSession(session.thread_id)}
                      onDoubleClick={() => {
                        setIsEditingTitle(session.thread_id);
                        setEditTitle(session.title);
                      }}
                    >
                      {session.title}
                    </h3>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.thread_id);
                    }}
                    className="text-gray-400 hover:text-red-400 transition-colors"
                  >
                    ×
                  </button>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  <div>メッセージ数: {session.message_count}</div>
                  <div>更新: {formatTimestamp(session.last_message_at)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* メインチャットエリア */}
      <div className="flex-1 flex flex-col">
        {/* ヘッダー */}
        <div className="bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              ☰
            </button>
            <div>
              <h1 className="text-xl font-bold text-blue-400">投票による協力グラフ</h1>
              <p className="text-sm text-gray-400">複数のAIエージェントが投票により最適な応答を決定</p>
              {currentSession && (
                <p className="text-xs text-gray-500 mt-1">
                  セッション: {currentSession.title}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* メッセージエリア */}
        <div className="flex-1 overflow-y-auto p-4">
          {conversations.length === 0 && !currentStreamingData && (
            <div className="text-center text-gray-400 mt-8">
              <div className="mb-4">
                <div className="text-6xl mb-2">🗳️</div>
                <h2 className="text-2xl font-bold mb-2">投票による協力グラフへようこそ</h2>
                <p className="text-lg mb-4">複数のAIエージェントが協力して最適な回答を提供します</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg max-w-2xl mx-auto">
                <h3 className="text-lg font-semibold mb-3 text-blue-400">仕組み</h3>
                <div className="text-left space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-blue-400">🧠</span>
                    <span>論理的思考エージェント - データと根拠に基づく分析</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-400">❤️</span>
                    <span>共感重視エージェント - 感情と人間らしさを重視</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-yellow-400">⚡</span>
                    <span>簡潔要約エージェント - 要点を明確に整理</span>
                  </div>
                  <div className="flex items-center space-x-2 pt-2">
                    <span className="text-purple-400">🗳️</span>
                    <span>各エージェントが相互評価し、投票により最適な回答を選出</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* 過去の会話 */}
          {conversations.map((conversation, index) => renderConversation(conversation, index))}
          
          {/* 現在のストリーミング会話 */}
          {currentStreamingData && renderConversation(currentStreamingData, -1)}
          
          {isLoading && !currentStreamingData && (
            <div className="flex justify-start">
              <div className="max-w-3xl p-4 rounded-lg bg-gray-700 text-gray-100">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                  <span>エージェントが協力して回答を作成中...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 入力エリア */}
        <div className="bg-gray-800 p-4 border-t border-gray-700">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="投票による協力エージェントに質問してください..."
              className="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!message.trim() || isLoading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              {isLoading ? '送信中...' : '送信'}
            </button>
          </form>
          <div className="text-xs text-gray-400 mt-2">
            Enterで送信、Shift+Enterで改行 | マークダウン対応
          </div>
        </div>
      </div>
    </div>
  );
};

export default VotingGraphPage; 