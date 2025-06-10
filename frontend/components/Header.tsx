import React from 'react';
import { Model } from '../types';
import ModelSelector from './ModelSelector';
import SparklesIcon from './icons/SparklesIcon';


interface HeaderProps {
  models: Model[];
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
  isLoading: boolean;
}

const Header: React.FC<HeaderProps> = ({ models, selectedModelId, onModelChange, isLoading }) => {
  return (
    <header className="bg-gradient-to-r from-gray-800 via-gray-900 to-black p-4 shadow-lg flex items-center justify-between sticky top-0 z-10 border-b border-gray-700">
      <div className="flex items-center">
        <SparklesIcon className="w-8 h-8 text-blue-400 mr-3" />
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-300">
          Gemini AI Chat
        </h1>
      </div>
      <div className="w-64">
        <ModelSelector
          models={models}
          selectedModelId={selectedModelId}
          onModelChange={onModelChange}
          disabled={isLoading}
        />
      </div>
    </header>
  );
};

export default Header;