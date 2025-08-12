import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const Landing = () => {
  const navigate = useNavigate();
  const { authenticated, user, organization } = useAuth();

  // Redirect authenticated users to appropriate page
  useEffect(() => {
    if (authenticated) {
      if (organization && organization.profile_completeness >= 50) {
        navigate('/dashboard');
      } else if (user && !user.org_name) {
        navigate('/onboarding');
      } else {
        navigate('/dashboard');
      }
    }
  }, [authenticated, user, organization, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
      {/* Navigation */}
      <nav className="flex justify-between items-center p-6 max-w-7xl mx-auto">
        <div className="flex items-center">
          <img 
            src="/assets/pink-lemonade-logo.png" 
            alt="Pink Lemonade" 
            className="h-12 w-auto"
          />
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-2 text-gray-700 hover:text-pink-600 font-medium transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="px-6 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 font-medium transition-colors"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center px-4 pt-20 pb-32">
        {/* Pink Lemonade Logo - Large */}
        <motion.div 
          className="mb-16"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
        >
          <img 
            src="/assets/pink-lemonade-logo.png" 
            alt="Pink Lemonade" 
            className="h-80 w-auto mx-auto"
          />
        </motion.div>

        {/* Main Heading */}
        <motion.div 
          className="max-w-4xl mb-8 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-4">
            <span className="text-gray-900">Change takes</span><br />
            <span className="text-gray-900">funding.</span><br />
            <span className="text-gray-900">Funding takes</span><br />
            <span className="text-gray-900">time.</span><br />
            <span className="text-pink-400">We save you</span><br />
            <span className="text-pink-400">both.</span>
          </h1>
        </motion.div>

        {/* Description */}
        <motion.p 
          className="text-xl md:text-2xl text-gray-600 max-w-2xl mb-12 leading-relaxed text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          With Pink Lemonade, you'll find, manage, and win more grants — without losing focus on the work that matters most.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div 
          className="flex flex-col sm:flex-row gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <button
            onClick={() => navigate('/register')}
            className="px-12 py-5 bg-gradient-to-r from-pink-500 to-pink-600 text-white text-xl font-semibold rounded-lg hover:from-pink-600 hover:to-pink-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Start Finding Grants
          </button>
          <button
            onClick={() => navigate('/login')}
            className="px-12 py-5 bg-white text-pink-600 text-xl font-semibold rounded-lg border-2 border-pink-500 hover:bg-pink-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Already Have Account?
          </button>
        </motion.div>

        {/* Features Preview */}
        <motion.div 
          className="mt-24 max-w-6xl grid grid-cols-1 md:grid-cols-3 gap-8"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-pink-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Powered Matching</h3>
            <p className="text-gray-600">Find the perfect grants for your organization with intelligent AI recommendations.</p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-pink-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M11 3.055A9.001 9.001 0 1020.945 9H11V3.055z" />
                <path d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Smart Tools Suite</h3>
            <p className="text-gray-600">Generate compelling narratives, impact reports, and grant pitches with AI assistance.</p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-pink-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Comprehensive Management</h3>
            <p className="text-gray-600">Track applications, deadlines, and success metrics in one centralized platform.</p>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-400">
            © 2025 Pink Lemonade. AI-powered grant management for nonprofits.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;