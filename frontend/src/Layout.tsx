import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import ModelSelector from '../components/ModelSelector';
import SparklesIcon from '../components/icons/SparklesIcon';
import { Model } from '../types';

export interface OutletContextProps {
  selectedModelId: string;
  isLoading: boolean;
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const Layout: React.FC = () => {
  const [models] = useState<Model[]>([
    { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash" },
    { id: "gemma-3-27b-it", name: "Gemma 3 (37B)" },
    { id: "gemma-3n-e4b-it", name: "Gemma 3N (E4B)" },
  ]);
  const [selectedModelId, setSelectedModelId] = useState<string>("gemini-1.5-flash");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100 font-sans">
      <nav className="bg-gradient-to-r from-gray-800 via-gray-900 to-black p-4 shadow-lg flex items-center justify-between sticky top-0 z-10 border-b border-gray-700">
        <div className="flex items-center">
            <SparklesIcon className="w-8 h-8 text-blue-400 mr-3" />
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-300">
                <Link to="/">Gemini AI Chat</Link>
            </h1>
        </div>
        <div className="flex items-center space-x-4">
            <ul className="flex space-x-4 items-center">
                <li>
                    <Link to="/" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                        Chat
                    </Link>
                </li>
                <li>
                    <Link to="/langchain-chat" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                        LangChain Chat
                    </Link>
                </li>
                <li>
                    <Link to="/about" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                        About
                    </Link>
                </li>
                <li>
                    <Link to="/new-page" className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                        New Page
                    </Link>
                </li>
            </ul>
            <div className="w-64">
                <ModelSelector
                    models={models}
                    selectedModelId={selectedModelId}
                    onModelChange={setSelectedModelId}
                    disabled={isLoading}
                />
            </div>
        </div>
      </nav>
      <main className="flex-grow flex flex-col overflow-hidden">
        <Outlet context={{ selectedModelId, isLoading, setIsLoading }} />
      </main>
    </div>
  );
};

export default Layout; 