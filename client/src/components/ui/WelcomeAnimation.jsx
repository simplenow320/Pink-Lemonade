import React, { useState, useEffect } from 'react';

const WelcomeAnimation = ({ userName = 'User', orgName = 'Your Organization', isFirstVisit = false }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // Trigger animation on mount
    setTimeout(() => setIsVisible(true), 100);
    setTimeout(() => setShowContent(true), 500);
  }, []);

  const getCurrentGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className={`
      transition-all duration-700 ease-out
      ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
    `}>
      <div className="bg-gradient-to-r from-pink-50 to-white rounded-2xl p-6 mb-6 border border-pink-100 shadow-sm">
        <div className="flex items-center space-x-4">
          {/* Animated Icon */}
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-pink-400 to-pink-600 rounded-xl flex items-center justify-center animate-float">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          
          {/* Welcome Content */}
          <div className="flex-1 min-w-0">
            <div className={`
              transition-all duration-500 delay-200
              ${showContent ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'}
            `}>
              <h2 className="text-lg font-semibold text-gray-900">
                {getCurrentGreeting()}, {userName}!
              </h2>
              <p className="text-sm text-gray-600 truncate">
                Welcome back to <span className="font-medium text-pink-600">{orgName}</span>
              </p>
            </div>
            
            {isFirstVisit && (
              <div className={`
                mt-2 transition-all duration-500 delay-400
                ${showContent ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'}
              `}>
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-pink-100 text-pink-700 text-xs font-medium">
                  <span className="w-2 h-2 bg-pink-400 rounded-full mr-2 animate-pulse"></span>
                  New here? Let's get you started!
                </div>
              </div>
            )}
          </div>
          
          {/* Quick Actions */}
          <div className={`
            hidden sm:flex items-center space-x-2 transition-all duration-500 delay-500
            ${showContent ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
          `}>
            <button className="p-2 text-gray-400 hover:text-pink-500 transition-colors duration-200 rounded-lg hover:bg-pink-50">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              </svg>
            </button>
            <button className="p-2 text-gray-400 hover:text-pink-500 transition-colors duration-200 rounded-lg hover:bg-pink-50">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Quick Stats Preview */}
        <div className={`
          mt-4 pt-4 border-t border-pink-100 transition-all duration-500 delay-600
          ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}
        `}>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold text-gray-900">12</div>
              <div className="text-xs text-gray-500">Active Grants</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-gray-900">85%</div>
              <div className="text-xs text-gray-500">Profile Done</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-gray-900">3</div>
              <div className="text-xs text-gray-500">New Matches</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeAnimation;