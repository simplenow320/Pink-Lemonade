import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      {/* Extra Large Logo */}
      <div className="mb-12 flex items-center">
        <svg className="w-24 h-24 mr-4" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="45" stroke="#EC4899" strokeWidth="5"/>
          <circle cx="50" cy="50" r="35" stroke="#EC4899" strokeWidth="3"/>
          {/* Lemon slice segments */}
          <path d="M50 15 L50 85" stroke="#EC4899" strokeWidth="2"/>
          <path d="M15 50 L85 50" stroke="#EC4899" strokeWidth="2"/>
          <path d="M25 25 L75 75" stroke="#EC4899" strokeWidth="2"/>
          <path d="M75 25 L25 75" stroke="#EC4899" strokeWidth="2"/>
          <circle cx="50" cy="50" r="8" fill="white" stroke="#EC4899" strokeWidth="2"/>
        </svg>
        <div>
          <h1 className="text-6xl font-bold">
            <span className="text-pink-500">pink</span>
          </h1>
          <h1 className="text-6xl font-bold -mt-2">
            <span className="text-pink-500">lemonade</span>
          </h1>
        </div>
      </div>

      {/* Main Heading */}
      <h2 className="text-4xl md:text-5xl font-bold text-center text-gray-900 max-w-3xl mb-8">
        Your Funding Shouldn't Feel Like a Full-Time Job
      </h2>

      {/* Description */}
      <p className="text-xl text-gray-600 text-center max-w-2xl mb-12">
        We help nonprofits discover, track, and secure grants with AI-powered tools 
        that simplify the entire funding process—so you can focus on your mission, not paperwork.
      </p>

      {/* CTA Button */}
      <button
        onClick={() => navigate('/grants')}
        className="px-12 py-5 bg-pink-500 text-white text-xl font-semibold rounded-lg hover:bg-pink-600 transition-colors shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
      >
        Find Funding Now
      </button>

      {/* Optional footer text */}
      <div className="mt-16 text-sm text-gray-400">
        Trusted by nonprofits nationwide • AI-powered grant matching • Real opportunities
      </div>
    </div>
  );
};

export default Landing;