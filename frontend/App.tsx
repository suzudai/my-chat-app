import React, { useState, useCallback } from 'react';
import { ChatMessage, Model } from './types';
import Header from './components/Header';
import ChatDisplay from './components/ChatDisplay';
import MessageInput from './components/MessageInput';
import ErrorMessage from './components/ErrorMessage';

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const models: Model[] = [
    // { id: "gemini-2.5-pro-preview-06-05", name: "Gemini 2.5 Pro Preview (06-05)" },
    // { id: "gemini-2.5-pro-preview-05-06", name: "Gemini 2.5 Pro Preview (05-06)" },
    // { id: "gemini-2.0-flash-lite", name: "Gemini 2.0 Flash Lite" },
    { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash" },
    { id: "gemma-3-27b-it", name: "Gemma 3 (37B)" },
    { id: "gemma-3n-e4b-it", name: "Gemma 3N (E4B)" },
  ];
  const [selectedModelId, setSelectedModelId] = useState<string>("gemini-1.5-flash");

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
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput, model: selectedModelId }),
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
  }, [selectedModelId]);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100 font-sans">
      <Header 
        models={models}
        selectedModelId={selectedModelId}
        onModelChange={setSelectedModelId}
        isLoading={isLoading}
      />
      <main className="flex-grow flex flex-col overflow-hidden">
        <ChatDisplay messages={messages} isLoading={isLoading} />
      </main>
      <div className="w-full md:w-2/3 mx-auto">
        {error && (
          <div className="px-4 sm:px-6 lg:px-8">
            <ErrorMessage message={error} />
          </div>
        )}
        <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default App;