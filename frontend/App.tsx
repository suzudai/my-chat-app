import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import SimpleChatPage from './src/pages/SimpleChatPage';
import AboutPage from './src/pages/AboutPage';
import NewPage from './src/pages/NewPage';
import ChatWithHistoryPage from './src/pages/ChatWithHistoryPage';
import ChatWithRagPage from './src/pages/ChatWithRagPage';
import ChatWithAgentsPage from './src/pages/ChatWithAgentsPage';
import VotingGraphPage from './src/pages/VotingGraphPage';
import Layout from './src/Layout';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SimpleChatPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="new-page" element={<NewPage />} />
          <Route path="langchain-chat" element={<ChatWithHistoryPage />} />
          <Route path="langchain-rag" element={<ChatWithRagPage />} />
          <Route path="deep-research" element={<ChatWithAgentsPage />} />
          <Route path="voting-graph" element={<VotingGraphPage />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;