import React, { useState, useEffect } from 'react';

const Grants = () => {
  console.log('Grants component is rendering!');
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900">Grants</h1>
      <p className="text-gray-600">Testing grants page - this should show up!</p>
      
      <div className="mt-4 bg-white shadow rounded-lg p-4">
        <p>If you can see this, the routing is working correctly.</p>
        <p>We will now add the actual grants functionality.</p>
      </div>
    </div>
  );
  

};

export default Grants;