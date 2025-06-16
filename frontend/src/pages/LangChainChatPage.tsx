import React, { useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ChatMessage } from '../../types';
import ChatDisplay from '../../components/ChatDisplay';
import MessageInput from '../../components/MessageInput';
import ErrorMessage from '../../components/ErrorMessage';
import { OutletContextProps } from '../../src/Layout';

const LangChainChatPage: React.FC = () => {
  const { isLoading, setIsLoading } = useOutletContext<OutletContextProps>();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

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
      const response = await fetch('/api/langchain/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
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
  }, [setIsLoading]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
        <div className="flex-grow overflow-y-auto p-4">
            <ChatDisplay messages={messages} isLoading={isLoading} />
        </div>
        <div className="w-full md:w-2/3 mx-auto p-4">
            {error && (
              <div className="pb-2">
                <ErrorMessage message={error} />
              </div>
            )}
            <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
    </div>
  );
};

export default LangChainChatPage; 