import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      {/* New Pink Lemonade Logo - 3.5x bigger, TOP CENTERED */}
      <div className="mb-12">
        <img 
          src="/assets/pink-lemonade-logo.png" 
          alt="Pink Lemonade" 
          className="h-96 w-auto mx-auto"
        />
      </div>
      {/* Main Heading */}
      <div className="max-w-4xl mb-8 text-center">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-4">
            <span className="text-gray-900">Change takes</span><br />
            <span className="text-gray-900">funding.</span><br />
            <span className="text-gray-900">Funding takes</span><br />
            <span className="text-gray-900">time.</span><br />
            <span className="text-pink-400">We save you</span><br />
            <span className="text-pink-400">both.</span>
          </h1>
        </div>

      {/* Description */}
      <p className="text-xl md:text-2xl text-gray-600 max-w-2xl mb-12 leading-relaxed text-center">
        With Pink Lemonade, you'll find, manage, and win more grants — without losing focus on the work that matters most.
      </p>

      {/* CTA Button */}
      <button
        onClick={() => navigate('/grants')}
        className="px-12 py-5 bg-pink-500 text-white text-xl font-semibold rounded-lg hover:bg-pink-600 transition-colors shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
      >
        Get Started
      </button>
    </div>
  );
};

export default Landing;