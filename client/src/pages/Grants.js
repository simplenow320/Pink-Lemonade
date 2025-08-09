import React, { useState, useEffect } from 'react';
import Toast from '../components/Toast';
import api from '../utils/api';

const Grants = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState(null);
  const [runningNow, setRunningNow] = useState(false);
  
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

  return (
    <div className="p-6">
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
          {runningNow ? 'Running...' : 'Run Now'}
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

      {/* Opportunities list */}
      <div className="bg-white shadow rounded-lg">
        {loading ? (
          <div className="p-8 text-center text-gray-500">
            Loading opportunities...
          </div>
        ) : opportunities.length > 0 ? (
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
                {grant.link && (
                  <a 
                    href={grant.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-pink-600 hover:text-pink-700 mt-2 inline-block"
                  >
                    View Details →
                  </a>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500 mb-4">No opportunities found</p>
            <p className="text-sm text-gray-400">
              Click "Run Now" to discover new grant opportunities
            </p>
          </div>
        )}
      </div>

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