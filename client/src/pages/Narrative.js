import React from 'react';
import { useParams, Link } from 'react-router-dom';

const Narrative = () => {
  const { grantId } = useParams();
  
  return (
    <div className="bg-white shadow-sm rounded-lg p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Grant Narrative</h1>
      <p className="text-gray-600 mb-4">This is a placeholder for the narrative editor for grant ID: {grantId}</p>
      <Link to={`/grants/${grantId}`} className="text-orange-600 hover:text-orange-700">
        &larr; Back to Grant
      </Link>
    </div>
  );
};

export default Narrative;