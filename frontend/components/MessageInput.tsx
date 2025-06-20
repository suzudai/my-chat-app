import React, { useState, useRef, useEffect } from 'react';
import PaperAirplaneIcon from './icons/PaperAirplaneIcon';
import LoadingSpinner from './LoadingSpinner';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

const MessageInput: React.FC<MessageInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  placeholder = "Type your message here..." 
}) => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // Set to scroll height
    }
  }, [inputValue]);
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };


  return (
    <form onSubmit={handleSubmit} className="px-4 sm:px-6 lg:px-8 pt-3 pb-5">
      <div className="flex items-end bg-gray-700 rounded-xl p-2">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          className="flex-grow p-3 bg-transparent text-gray-100 placeholder-gray-400 focus:outline-none resize-none overflow-y-auto max-h-32 custom-scrollbar"
          disabled={isLoading}
          style={{ scrollbarWidth: 'thin' }} 
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="ml-3 p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
          aria-label="Send message"
        >
          {isLoading ? <LoadingSpinner className="w-5 h-5" /> : <PaperAirplaneIcon className="w-5 h-5" />}
        </button>
      </div>
    </form>
  );
};

export default MessageInput;