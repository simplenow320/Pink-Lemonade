import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Toast from '../components/Toast';
import SourceBadge from '../components/SourceBadge';
import api from '../utils/api';

const Grants = () => {
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState(null);
  const [runningNow, setRunningNow] = useState(false);
  const [showProfilePrompt, setShowProfilePrompt] = useState(false);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  // Get organization ID (hardcoded for now, should come from context/auth)
  const orgId = 1; // TODO: Get from user context

  // Fetch opportunities using matching endpoint
  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      // Try new matching endpoint first
      const matchingResponse = await api.get(`/matching?orgId=${orgId}&limit=50`);
      if (matchingResponse.data) {
        // Combine federal and news results
        const federal = matchingResponse.data.federal || [];
        const news = matchingResponse.data.news || [];
        const combined = [...federal, ...news].sort((a, b) => (b.score || 0) - (a.score || 0));
        setOpportunities(combined);
        return;
      }
    } catch (error) {
      console.log('Matching endpoint not available, falling back to opportunities');
    }
    
    // Fallback to original opportunities endpoint
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

  // Handle federal item click for details
  const handleFederalClick = async (grant) => {
    if (grant.opportunity_number) {
      try {
        const response = await api.get(`/matching/detail/grants-gov/${grant.opportunity_number}`);
        setSelectedGrant(response.data);
        setShowModal(true);
      } catch (error) {
        console.error('Error fetching grant details:', error);
        setToast({
          message: 'Failed to load grant details',
          type: 'error'
        });
      }
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
              {opportunities.map((grant, index) => (
                <GrantCard 
                  key={grant.id || index} 
                  grant={grant} 
                  onFederalClick={handleFederalClick}
                />
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

      {/* Grant Detail Modal */}
      {showModal && selectedGrant && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Grant Details</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto">
              <h4 className="font-semibold text-gray-900 mb-2">{selectedGrant.title}</h4>
              <p className="text-gray-600 mb-4">{selectedGrant.description}</p>
              {selectedGrant.eligibility && (
                <div className="mb-4">
                  <h5 className="font-medium text-gray-900 mb-1">Eligibility</h5>
                  <p className="text-sm text-gray-600">{selectedGrant.eligibility}</p>
                </div>
              )}
              {selectedGrant.sourceNotes && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <h6 className="text-xs font-medium text-gray-700 mb-1">Source</h6>
                  <p className="text-xs text-gray-600">
                    API: {selectedGrant.sourceNotes.api} | 
                    Endpoint: {selectedGrant.sourceNotes.endpoint} | 
                    ID: {selectedGrant.sourceNotes.opportunityNumber}
                  </p>
                </div>
              )}
            </div>
          </div>
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

// Intelligence Insights Component
const IntelligenceInsights = ({ intelligence }) => {
  const [showInsights, setShowInsights] = useState(false);
  
  if (!intelligence?.intelligence_available) {
    return null;
  }

  const formatAmount = (amount) => {
    if (!amount || amount === 0) return 'Variable';
    return `$${amount.toLocaleString()}`;
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getConfidenceText = (score) => {
    if (score >= 0.7) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Limited';
  };

  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <button
        onClick={(e) => {
          e.stopPropagation();
          setShowInsights(!showInsights);
        }}
        className="flex items-center text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors"
      >
        <span className="mr-1">🧠</span>
        Funding Intelligence
        <span className="ml-1">{showInsights ? '▲' : '▼'}</span>
      </button>
      
      {showInsights && (
        <div className="mt-2 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100">
          <div className="space-y-2">
            {/* Historical Context */}
            {intelligence.total_awards > 0 && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-purple-700 mr-2">📊</span>
                <span className="text-xs text-gray-700">
                  Funder awarded {intelligence.total_awards} similar grants in past 3 years
                  {intelligence.average_amount > 0 && ` (avg: ${formatAmount(intelligence.average_amount)})`}
                </span>
              </div>
            )}

            {/* Timing Insights */}
            {intelligence.timing_recommendation && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-blue-700 mr-2">⏰</span>
                <span className="text-xs text-gray-700">
                  {intelligence.timing_recommendation}
                </span>
              </div>
            )}

            {/* Success Indicators */}
            {intelligence.success_indicators && intelligence.success_indicators.length > 0 && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-green-700 mr-2">✅</span>
                <span className="text-xs text-gray-700">
                  {intelligence.success_indicators[0]}
                </span>
              </div>
            )}

            {/* Match Likelihood */}
            {intelligence.match_likelihood > 0 && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-orange-700 mr-2">🎯</span>
                <span className="text-xs text-gray-700">
                  {intelligence.match_likelihood}% alignment with your organization profile
                </span>
              </div>
            )}

            {/* Strategic Actions */}
            {intelligence.strategic_actions && intelligence.strategic_actions.length > 0 && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-indigo-700 mr-2">💡</span>
                <span className="text-xs text-gray-700">
                  {intelligence.strategic_actions[0]}
                </span>
              </div>
            )}

            {/* Confidence & Freshness */}
            <div className="flex justify-between items-center pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500">
                Confidence: <span className={`font-medium ${getConfidenceColor(intelligence.confidence_score)}`}>
                  {getConfidenceText(intelligence.confidence_score)}
                </span>
              </span>
              {intelligence.generated_at && (
                <span className="text-xs text-gray-500">
                  Updated: {new Date(intelligence.generated_at).toLocaleDateString()}
                </span>
              )}
            </div>

            {/* Intelligence Summary */}
            {intelligence.intelligence_summary && (
              <div className="pt-2 border-t border-gray-200">
                <span className="text-xs text-gray-600 italic">
                  {intelligence.intelligence_summary}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Grant Card Component with Sources toggle
const GrantCard = ({ grant, onFederalClick }) => {
  const [showSources, setShowSources] = useState(false);
  
  const handleCardClick = () => {
    // If it's a federal grant, show details
    if (grant.opportunity_number) {
      onFederalClick(grant);
    }
  };

  return (
    <div className="p-4 hover:bg-gray-50">
      <div className="flex justify-between items-start">
        <div 
          className="flex-1 cursor-pointer" 
          onClick={handleCardClick}
        >
          <h3 className="font-semibold text-gray-900">{grant.title}</h3>
          <p className="text-sm text-gray-600 mt-1">
            {grant.funder || grant.agency || grant.source || 'Source'}
          </p>
          {grant.deadline && (
            <p className="text-sm text-gray-500 mt-1">
              Deadline: {new Date(grant.deadline).toLocaleDateString()}
            </p>
          )}
          {grant.posted_date && (
            <p className="text-sm text-gray-500 mt-1">
              Posted: {new Date(grant.posted_date).toLocaleDateString()}
            </p>
          )}
          {(grant.amount_min || grant.award_ceiling) && (
            <p className="text-sm text-gray-500">
              Amount: ${(grant.amount_min || grant.award_ceiling || 0).toLocaleString()}
              {grant.amount_max && ` - $${grant.amount_max.toLocaleString()}`}
            </p>
          )}
        </div>
        <div className="ml-4 flex flex-col items-end space-y-2">
          {(grant.score || grant.match_score) && (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              (grant.score || grant.match_score) >= 80 ? 'bg-green-100 text-green-800' :
              (grant.score || grant.match_score) >= 60 ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              Score: {grant.score || grant.match_score}{grant.score ? '%' : '/5'}
            </span>
          )}
          {grant.sourceNotes && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowSources(!showSources);
              }}
              className="text-xs text-blue-600 hover:text-blue-700"
            >
              Sources {showSources ? '▲' : '▼'}
            </button>
          )}
        </div>
      </div>
      
      {/* Sources section */}
      {showSources && grant.sourceNotes && (
        <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600">
          <strong>Source:</strong> {grant.sourceNotes.api}<br/>
          {grant.sourceNotes.endpoint && <><strong>Endpoint:</strong> {grant.sourceNotes.endpoint}<br/></>}
          {grant.sourceNotes.query && <><strong>Query:</strong> {grant.sourceNotes.query}<br/></>}
          {grant.sourceNotes.opportunityNumber && <><strong>ID:</strong> {grant.sourceNotes.opportunityNumber}<br/></>}
          {grant.sourceNotes.window && <><strong>Window:</strong> {grant.sourceNotes.window}</>}
        </div>
      )}
      
      {/* Intelligence Insights */}
      <IntelligenceInsights intelligence={grant.historical_intelligence} />
      
      <div className="flex justify-between items-center gap-3 mt-2">
        <div className="flex gap-3">
          {grant.id && grant.id > 0 ? (
            <Link 
              to={`/grant/${grant.id}`}
              className="text-sm text-pink-600 hover:text-pink-700"
            >
              Analyze Grant →
            </Link>
          ) : (
            <span className="text-sm text-gray-400 cursor-not-allowed">
              Analyze Grant →
            </span>
          )}
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
        
        {/* Source Badge */}
        <SourceBadge 
          source_name={grant.source_name || grant.source} 
          source_url={grant.source_url || grant.link}
        />
      </div>
    </div>
  );
};

export default Grants;