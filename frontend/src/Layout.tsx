import React, { useState, useMemo, useEffect } from 'react';
import { Outlet, Link, NavLink, useLocation } from 'react-router-dom';
import ModelSelector from '../components/ModelSelector';
import SparklesIcon from '../components/icons/SparklesIcon';
import { Model } from '../types';

export interface OutletContextProps {
  selectedModelId: string;
  isLoading: boolean;
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const Layout: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const location = useLocation();

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('/api/langchain/models');
        if (!response.ok) {
          throw new Error('Failed to fetch models');
        }
        const data: Model[] = await response.json();
        setModels(data);
        if (data.length > 0) {
          setSelectedModelId(data[0].id);
        }
      } catch (error) {
        console.error("Error fetching models:", error);
        // ここでエラーハンドリングをすることもできます（例：エラーメッセージを表示）
      }
    };
    fetchModels();
  }, []);

  const modelsForSelector = useMemo(() => {
    if (location.pathname === '/langchain-chat') {
      const disabledModels = ["gemma-3-27b-it", "gemma-3n-e4b-it"];
      return models.map(model => ({
        ...model,
        disabled: disabledModels.includes(model.id),
      }));
    }
    return models;
  }, [models, location.pathname]);

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
                    <NavLink to="/" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'}`} end>
                        Chat
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/langchain-chat" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                        LangChain Chat
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/about" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                        About
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/new-page" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                        New Page
                    </NavLink>
                </li>
            </ul>
            <div className="w-64">
                <ModelSelector
                    models={modelsForSelector}
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