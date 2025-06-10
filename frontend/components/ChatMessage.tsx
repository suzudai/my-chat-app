import React from 'react';
import { ChatMessage as ChatMessageType } from '../types';
import UserIcon from './icons/UserIcon';
import SparklesIcon from './icons/SparklesIcon';
import LoadingSpinner from './LoadingSpinner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const isStreaming = message.streaming;
  const isError = message.error;

  const Icon = isUser ? UserIcon : SparklesIcon;
  const bgColor = isUser ? 'bg-blue-600' : (isError ? 'bg-red-700/80' : 'bg-gray-700');
  const textColor = isUser ? 'text-white' : (isError ? 'text-gray-100' : 'text-gray-100');
  const alignment = isUser ? 'items-end' : 'items-start';

  return (
    <div className={`flex flex-col ${alignment} mb-4 animate-fadeIn`}>
      <div className={`flex items-start max-w-xl lg:max-w-2xl xl:max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 p-2 rounded-full ${isUser ? 'bg-blue-500 ml-2' : 'bg-teal-500 mr-2'} `}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div
          className={`px-4 py-3 rounded-xl ${bgColor} ${textColor} shadow-md`}
        >
          {isError && <p className="font-bold mb-1">An error occurred.</p>}
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.text}</p>
          ) : (
            <div className="prose prose-invert max-w-none prose-p:whitespace-pre-wrap">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300" />,
                  code({node, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '')
                    return match ? (
                      <div className="bg-gray-800 rounded-md my-2">
                        <div className="bg-gray-900 text-gray-400 text-xs px-3 py-1 rounded-t-md">
                          {match[1]}
                        </div>
                        <pre className="p-3 overflow-x-auto text-sm">
                          <code {...props} className={className}>{children}</code>
                        </pre>
                      </div>
                    ) : (
                      <code {...props} className={`${className || ''} bg-gray-800 rounded-sm px-1.5 py-0.5 text-red-300`}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          )}
          {isStreaming && !isError && (
            <div className="flex items-center justify-start mt-2">
              <LoadingSpinner className="w-4 h-4 mr-2 text-gray-300" />
              <span className="text-xs text-gray-400">AI is thinking...</span>
            </div>
          )}
        </div>
      </div>
      <p className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right mr-12' : 'text-left ml-12'}`}>
        {message.timestamp.toLocaleTimeString()}
      </p>
       <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default ChatMessage;