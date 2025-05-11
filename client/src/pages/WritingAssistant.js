import React from 'react';
import { useParams, Link } from 'react-router-dom';

const WritingAssistant = () => {
  const { grantId } = useParams();
  
  return (
    <div className="bg-white shadow-sm rounded-lg p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">AI Writing Assistant</h1>
      {grantId ? (
        <>
          <p className="text-gray-600 mb-4">This is a placeholder for the writing assistant for grant ID: {grantId}</p>
          <Link to={`/grants/${grantId}`} className="text-orange-600 hover:text-orange-700">
            &larr; Back to Grant
          </Link>
        </>
      ) : (
        <p className="text-gray-600 mb-4">This is a placeholder for the general writing assistant page.</p>
      )}
    </div>
  );
};

export default WritingAssistant;