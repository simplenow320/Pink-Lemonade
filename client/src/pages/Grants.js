import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Toast from '../components/Toast';
import api from '../utils/api';

const Grants = () => {
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState(null);
  const [runningNow, setRunningNow] = useState(false);
  const [showProfilePrompt, setShowProfilePrompt] = useState(false);
  
  // Get organization ID (hardcoded for now, should come from context/auth)
  const orgId = 1; // TODO: Get from user context

  // Fetch opportunities
  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/opportunities?orgId=${orgId}`);
      setOpportunities(response.data.opportunities || []);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
      setToast({
        message: 'Failed to load opportunities',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // Run scraper now
  const handleRunNow = async () => {
    setRunningNow(true);
    try {
      const payload = {
        orgId: orgId
      };
      
      if (searchQuery) {
        payload.query = searchQuery;
      }

      const response = await api.post('/scrape/run-now', payload);
      const { upserted, mode } = response.data;
      
      // Show success toast
      setToast({
        message: `Upserted ${upserted} opportunities in ${mode} mode`,
        type: 'success'
      });
      
      // Refresh opportunities list
      await fetchOpportunities();
      
    } catch (error) {
      console.error('Error running scraper:', error);
      setToast({
        message: 'Failed to run scraper. Please try again.',
        type: 'error'
      });
    } finally {
      setRunningNow(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchOpportunities();
  }, []);

  // Check if user should see profile completion prompt
  useEffect(() => {
    const checkUserProfile = async () => {
      try {
        const response = await fetch('/api/organization/get', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          // Show prompt if organization profile is incomplete
          const org = data.organization;
          const isIncomplete = !org?.mission || !org?.primary_focus_areas || 
                              org?.primary_focus_areas?.length === 0;
          setShowProfilePrompt(isIncomplete && opportunities.length > 0);
        }
      } catch (error) {
        console.error('Error checking profile:', error);
      }
    };
    
    if (opportunities.length > 0) {
      checkUserProfile();
    }
  }, [opportunities]);

  // Show welcome state for first-time users
  if (!loading && opportunities.length === 0 && !runningNow) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
        <div className="max-w-4xl mx-auto px-4 py-16">
          {/* Welcome Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Discover Your Perfect Grants
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We'll search thousands of funding opportunities tailored specifically to your organization's mission and needs
            </p>
          </div>

          {/* Action Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <div className="text-center">
              {/* Icon */}
              <div className="w-20 h-20 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                Ready to Find Funding?
              </h2>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Click the button below to instantly discover grant opportunities matched to your organization
              </p>

              {/* Search Input (Optional) */}
              <div className="max-w-md mx-auto mb-6">
                <input
                  type="text"
                  placeholder="Search for specific grants (optional)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
              </div>

              {/* CTA Button */}
              <button
                onClick={handleRunNow}
                className="px-8 py-4 bg-pink-500 text-white text-lg font-semibold rounded-lg hover:bg-pink-600 transition-all transform hover:scale-105 shadow-lg"
              >
                Discover Grants Now
              </button>
            </div>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-pink-500 text-3xl mb-2">🎯</div>
              <h3 className="font-semibold text-gray-900 mb-1">Smart Matching</h3>
              <p className="text-sm text-gray-600">AI-powered matching based on your organization profile</p>
            </div>
            <div className="text-center">
              <div className="text-pink-500 text-3xl mb-2">🔄</div>
              <h3 className="font-semibold text-gray-900 mb-1">Real-Time Updates</h3>
              <p className="text-sm text-gray-600">Fresh opportunities from multiple trusted sources</p>
            </div>
            <div className="text-center">
              <div className="text-pink-500 text-3xl mb-2">📊</div>
              <h3 className="font-semibold text-gray-900 mb-1">Track & Manage</h3>
              <p className="text-sm text-gray-600">Save favorites and track application progress</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Regular view when grants are loaded
  return (
    <div className="p-6">
      {/* Profile completion prompt for new users */}
      {showProfilePrompt && (
        <div className="mb-6 bg-gradient-to-r from-pink-50 to-purple-50 border border-pink-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-pink-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-gray-900">Improve Your Grant Matches!</h3>
              <p className="mt-1 text-gray-600">
                Complete your organization profile to get better grant recommendations tailored to your mission and focus areas.
              </p>
              <div className="mt-4 flex items-center space-x-3">
                <button
                  onClick={() => navigate('/organization')}
                  className="px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors font-medium"
                >
                  Complete Profile
                </button>
                <button
                  onClick={() => setShowProfilePrompt(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Later
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header with Run Now button */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Grant Opportunities</h1>
          <p className="text-gray-600">Discover and manage funding opportunities</p>
        </div>
        
        <button
          onClick={handleRunNow}
          disabled={runningNow}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            runningNow 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : 'bg-pink-500 text-white hover:bg-pink-600'
          }`}
        >
          {runningNow ? 'Discovering...' : 'Refresh Grants'}
        </button>
      </div>

      {/* Search bar */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search for specific grants (optional)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
        />
      </div>

      {/* Loading state */}
      {(loading || runningNow) && (
        <div className="bg-white shadow rounded-lg p-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4"></div>
            <p className="text-gray-600 text-lg font-medium">
              {runningNow ? 'Discovering new grant opportunities...' : 'Loading opportunities...'}
            </p>
            <p className="text-gray-500 text-sm mt-2">This may take a few moments</p>
          </div>
        </div>
      )}

      {/* Opportunities list */}
      {!loading && !runningNow && (
        <div className="bg-white shadow rounded-lg">
          {opportunities.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {opportunities.map((grant) => (
                <div key={grant.id} className="p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{grant.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{grant.funder}</p>
                      {grant.deadline && (
                        <p className="text-sm text-gray-500 mt-1">
                          Deadline: {new Date(grant.deadline).toLocaleDateString()}
                        </p>
                      )}
                      {grant.amount_min && (
                        <p className="text-sm text-gray-500">
                          Amount: ${grant.amount_min.toLocaleString()}
                          {grant.amount_max && ` - $${grant.amount_max.toLocaleString()}`}
                        </p>
                      )}
                    </div>
                    {grant.match_score && (
                      <div className="ml-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          grant.match_score >= 4 ? 'bg-green-100 text-green-800' :
                          grant.match_score >= 3 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          Score: {grant.match_score}/5
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-3 mt-2">
                    <Link 
                      to={`/grant/${grant.id}`}
                      className="text-sm text-pink-600 hover:text-pink-700"
                    >
                      Analyze Grant →
                    </Link>
                    {grant.link && (
                      <a 
                        href={grant.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-gray-600 hover:text-gray-700"
                      >
                        Official Page ↗
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">No opportunities found</p>
              <p className="text-sm text-gray-400">
                Try adjusting your search or click "Refresh Grants" to discover new opportunities
              </p>
            </div>
          )}
        </div>
      )}

      {/* Toast notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default Grants;