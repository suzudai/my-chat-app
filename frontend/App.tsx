import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import HomePage from './src/pages/HomePage';
import AboutPage from './src/pages/AboutPage';
import NewPage from './src/pages/NewPage';
import LangChainChatPage from './src/pages/LangChainChatPage';
import LangChainChatRagPage from './src/pages/LangChainChatRagPage';
import Layout from './src/Layout';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="new-page" element={<NewPage />} />
          <Route path="langchain-chat" element={<LangChainChatPage />} />
          <Route path="langchain-rag" element={<LangChainChatRagPage />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;