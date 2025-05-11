import React from 'react';
import { useParams, Link } from 'react-router-dom';

const GrantDetail = () => {
  const { id } = useParams();
  
  return (
    <div className="bg-white shadow-sm rounded-lg p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Grant Detail Page</h1>
      <p className="text-gray-600 mb-4">This is a placeholder for grant ID: {id}</p>
      <Link to="/grants" className="text-orange-600 hover:text-orange-700">
        &larr; Back to Grants
      </Link>
    </div>
  );
};

export default GrantDetail;