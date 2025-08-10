import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      {/* Pink Lemonade Logo - 3.5x bigger, centered */}
      <div className="mb-12">
        <img 
          src="/assets/pink-lemonade-logo.png" 
          alt="Pink Lemonade" 
          className="h-96 w-auto mx-auto"
        />
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