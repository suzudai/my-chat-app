import React from 'react';

const AboutPage: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto">
        <div className="p-8 text-white">
          <h1 className="text-2xl font-bold mb-4">About This Application</h1>
          <p>
            This is a chat application powered by Gemini and built with React and FastAPI.
          </p>
        </div>
    </div>
  );
};

export default AboutPage; 