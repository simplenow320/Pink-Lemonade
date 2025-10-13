import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const GrantNotFound = () => {
  const navigate = useNavigate();
  const { id } = useParams();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
        <div className="mb-6">
          <svg className="mx-auto h-16 w-16 text-pink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          Grant Not Found
        </h2>
        
        <p className="text-gray-600 mb-2">
          Grant ID {id} does not exist or has been removed.
        </p>
        
        <p className="text-sm text-gray-500 mb-6">
          This could happen if the grant was deleted or the link is outdated.
        </p>
        
        <div className="space-y-3">
          <button
            onClick={() => navigate('/grants')}
            className="w-full bg-pink-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-pink-700 transition"
          >
            Browse Available Grants
          </button>
          
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default GrantNotFound;
