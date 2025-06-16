import React from 'react';
import { ChatMessage as ChatMessageType } from '../types';
import UserIcon from './icons/UserIcon';
import SparklesIcon from './icons/SparklesIcon';
import LoadingSpinner from './LoadingSpinner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CopyIcon from './icons/CopyIcon';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
            <div className="prose prose-invert max-w-none prose-p:whitespace-pre-wrap prose-headings:text-gray-100 prose-strong:text-gray-100 prose-em:text-gray-300 prose-code:before:content-[''] prose-code:after:content-['']">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300" />,
                  h1: ({node, ...props}) => <h1 {...props} className="text-3xl font-bold mt-6 mb-4 text-gray-100" />,
                  h2: ({node, ...props}) => <h2 {...props} className="text-2xl font-bold mt-5 mb-3 text-gray-100" />,
                  h3: ({node, ...props}) => <h3 {...props} className="text-xl font-bold mt-4 mb-2 text-gray-100" />,
                  h4: ({node, ...props}) => <h4 {...props} className="text-lg font-bold mt-3 mb-2 text-gray-100" />,
                  h5: ({node, ...props}) => <h5 {...props} className="text-base font-bold mt-2 mb-1 text-gray-100" />,
                  h6: ({node, ...props}) => <h6 {...props} className="text-sm font-bold mt-2 mb-1 text-gray-100" />,
                  ul: ({node, ...props}) => <ul {...props} className="list-disc list-outside pl-6 mb-4 space-y-1" />,
                  ol: ({node, ...props}) => <ol {...props} className="list-decimal list-outside pl-6 mb-4 space-y-1" />,
                  li: ({node, children, ...props}) => {
                    // チェックボックスリスト項目の場合
                    if (Array.isArray(children) && children.length > 0 && 
                        typeof children[0] === 'object' && 
                        children[0] !== null && 
                        'props' in children[0] && 
                        children[0].props?.type === 'checkbox') {
                      return (
                        <li {...props} className="text-gray-200 flex items-center space-x-2 list-none -ml-6">
                          {children}
                        </li>
                      );
                    }
                    return <li {...props} className="text-gray-200">{children}</li>;
                  },
                  input: ({node, ...props}) => {
                    if (props.type === 'checkbox') {
                      return <input {...props} className="mr-2 h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500" />;
                    }
                    return <input {...props} />;
                  },
                  blockquote: ({node, ...props}) => <blockquote {...props} className="border-l-4 border-gray-500 pl-4 my-4 italic text-gray-300" />,
                  table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table {...props} className="min-w-full border border-gray-600" /></div>,
                  th: ({node, ...props}) => <th {...props} className="border border-gray-600 px-3 py-2 bg-gray-700 font-bold text-gray-100" />,
                  td: ({node, ...props}) => <td {...props} className="border border-gray-600 px-3 py-2 text-gray-200" />,
                  p: ({node, ...props}) => <p {...props} className="mb-3 text-gray-200" />,
                  hr: ({node, ...props}) => <hr {...props} className="my-6 border-gray-600" />,
                  code({node, className, children, ...props}) {
                    const [isCopied, setIsCopied] = React.useState(false);

                    const handleCopy = () => {
                      if (!children) return;
                      const codeToCopy = String(children).replace(/\\n$/, '');
                      navigator.clipboard.writeText(codeToCopy).then(() => {
                        setIsCopied(true);
                        setTimeout(() => setIsCopied(false), 2000);
                      });
                    };

                    const match = /language-(\w+)/.exec(className || '')
                    return match ? (
                      <div className="my-2 text-left">
                        <div className="text-gray-400 text-xs flex items-center justify-between mb-2">
                          <span className="italic">{match[1]}</span>
                          <button onClick={handleCopy} className={`flex items-center space-x-1 transition-colors duration-200 ${isCopied ? 'text-green-400' : 'text-gray-400 hover:text-white'}`} disabled={isCopied}>
                            <CopyIcon className="w-4 h-4" />
                            <span>{isCopied ? 'コピーしました' : 'コピーする'}</span>
                          </button>
                        </div>
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                        >
                          {String(children).replace(/\\n$/, '')}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className={`${className || ''} bg-gray-800 rounded-sm px-1.5 py-0.5 text-red-300`} {...props}>
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