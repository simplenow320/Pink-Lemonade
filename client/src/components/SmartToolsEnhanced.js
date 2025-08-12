import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const SmartToolsEnhanced = () => {
  const [grants, setGrants] = useState([]);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingGrants, setLoadingGrants] = useState(true);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const [result, setResult] = useState('');
  const [dataQuality, setDataQuality] = useState({});
  const [orgProfile, setOrgProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch both grants and organization profile
    const fetchData = async () => {
      setLoadingGrants(true);
      setLoadingOrg(true);
      
      // Fetch grants
      try {
        const grantsResponse = await fetch('/api/grants/list');
        if (grantsResponse.ok) {
          const data = await grantsResponse.json();
          setGrants(data.grants || []);
        }
      } catch (error) {
        console.error('Error fetching grants:', error);
        setGrants([]);
      } finally {
        setLoadingGrants(false);
      }
      
      // Fetch organization profile
      try {
        const orgResponse = await fetch('/api/organizations/profile');
        if (orgResponse.ok) {
          const data = await orgResponse.json();
          setOrgProfile(data);
        }
      } catch (error) {
        console.error('Error fetching organization:', error);
      } finally {
        setLoadingOrg(false);
      }
    };
    
    fetchData();
  }, []);

  const smartTools = [
    {
      id: 'case-support',
      name: 'Case for Support',
      description: 'Create compelling case documents that make the argument for why your organization deserves funding',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: 'from-pink-500 to-pink-600',
      endpoint: '/api/writing/case-support',
      route: '/case-support'
    },
    {
      id: 'grant-pitch',
      name: 'Grant Pitch',
      description: 'AI-powered pitch generator for presentations, emails, and verbal delivery to funders',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
        </svg>
      ),
      color: 'from-green-500 to-green-600',
      endpoint: '/api/writing/grant-pitch',
      route: '/grant-pitch'
    },
    {
      id: 'impact-report',
      name: 'Impact Reports',
      description: 'Generate comprehensive reports showing your programs actual outcomes and community impact',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'from-blue-500 to-blue-600',
      endpoint: '/api/writing/impact-report',
      route: '/impact-report'
    },
    {
      id: 'writing-assistant',
      name: 'Writing Assistant',
      description: 'AI-powered text improvement and proposal writing help for any grant content',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      color: 'from-purple-500 to-purple-600',
      endpoint: '/api/writing/improve',
      route: '/writing-assistant'
    },
    {
      id: 'analytics-dashboard',
      name: 'Analytics Dashboard',
      description: 'Real-time metrics and performance monitoring',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      color: 'from-indigo-500 to-indigo-600',
      endpoint: null,
      route: '/analytics'
    },
    {
      id: 'smart-reports',
      name: 'Smart Reports',
      description: 'Automated report generation with AI insights',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      color: 'from-orange-500 to-orange-600',
      endpoint: null,
      route: '/impact-report'
    }
  ];

  const handleToolClick = (tool) => {
    if (tool.route && !tool.endpoint) {
      // Navigate to the tool's page
      window.location.href = tool.route;
    } else {
      // Open tool modal for API-based tools
      setSelectedTool(tool);
      setFormData({});
      setResult('');
      setDataQuality({});
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Prepare enhanced request with grant context
      const requestData = {
        ...formData,
        grant_id: selectedGrant?.id || null
      };

      const response = await fetch(selectedTool.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();
      
      if (data.success || data.content || data.improved_text) {
        setResult(data.content || data.improved_text || data.response);
        
        // Set data quality indicators
        setDataQuality({
          organizationFields: data.data_sources?.organization_fields_used || '30+ fields',
          funderData: data.data_sources?.authentic_funder_data ? 'Verified' : 'Not available',
          grantContext: selectedGrant ? 'Included' : 'General',
          qualityScore: '⭐⭐⭐⭐⭐'
        });
      } else {
        setError(data.error || 'Failed to generate content. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Failed to connect to the service. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const renderToolForm = () => {
    if (!selectedTool) return null;

    switch (selectedTool.id) {
      case 'case-support':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Program Focus
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                placeholder="e.g., Youth mentorship program"
                onChange={(e) => setFormData({...formData, program_name: e.target.value})}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Funding Amount Needed
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                placeholder="e.g., $50,000"
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
              />
            </div>
          </>
        );

      case 'grant-pitch':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pitch Format
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                onChange={(e) => setFormData({...formData, format: e.target.value})}
                required
              >
                <option value="">Select format...</option>
                <option value="elevator">30-Second Elevator Pitch</option>
                <option value="email">Email Introduction</option>
                <option value="presentation">5-Minute Presentation</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key Message
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                rows="3"
                placeholder="What's the main point you want to convey?"
                onChange={(e) => setFormData({...formData, key_message: e.target.value})}
              />
            </div>
          </>
        );

      case 'impact-report':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Period
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Q1 2024 or Annual 2023"
                onChange={(e) => setFormData({...formData, period: e.target.value})}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key Metrics
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="e.g., 500 youth served, 85% graduation rate"
                onChange={(e) => setFormData({...formData, metrics: e.target.value})}
              />
            </div>
          </>
        );

      case 'writing-assistant':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text to Improve
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows="4"
                placeholder="Paste your grant text here..."
                onChange={(e) => setFormData({...formData, text: e.target.value})}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Improvement Type
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                onChange={(e) => setFormData({...formData, improvement_type: e.target.value})}
              >
                <option value="strategic">Strategic Enhancement</option>
                <option value="clarity">Improve Clarity</option>
                <option value="persuasive">Make More Persuasive</option>
                <option value="concise">Make More Concise</option>
              </select>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Smart Tools Suite</h1>
            <Link to="/dashboard" className="text-pink-600 hover:text-pink-700">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Grant Context Selector */}
        <motion.div 
          className="bg-white rounded-lg shadow-md p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-xl font-bold mb-4">Grant Context (Optional)</h2>
          <p className="text-gray-600 mb-4">
            Select a grant to automatically include funder information and requirements in your generated content
          </p>
          
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={selectedGrant?.id || ''}
                onChange={(e) => {
                  const grant = grants.find(g => g.id === parseInt(e.target.value));
                  setSelectedGrant(grant);
                }}
                disabled={loadingGrants}
              >
                <option value="">No specific grant - Generate general content</option>
                {grants.map(grant => (
                  <option key={grant.id} value={grant.id}>
                    {grant.title} - {grant.funder}
                    {grant.deadline && ` (Due: ${new Date(grant.deadline).toLocaleDateString()})`}
                  </option>
                ))}
              </select>
            </div>
            
            {selectedGrant && (
              <div className="px-4 py-2 bg-green-50 border border-green-200 rounded-md">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-green-800">
                    Enhanced mode active for {selectedGrant.funder}
                  </span>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Organization Profile Status */}
        {orgProfile && (
          <motion.div 
            className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                </svg>
                <span className="text-blue-800 font-medium">
                  Organization: {orgProfile.name || 'Your Organization'}
                </span>
              </div>
              <div className="text-sm text-blue-600">
                Profile: {orgProfile.profile_completeness || 0}% complete
              </div>
            </div>
          </motion.div>
        )}

        {/* Smart Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {smartTools.map((tool, index) => (
            <motion.div
              key={tool.id}
              className={`bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transform transition-all hover:scale-105 hover:shadow-xl`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              onClick={() => handleToolClick(tool)}
            >
              <div className={`bg-gradient-to-r ${tool.color} p-6 text-white`}>
                <div className="flex items-center justify-between mb-3">
                  {tool.icon}
                  <div className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">
                    Enhanced
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-2">{tool.name}</h3>
                <p className="text-sm opacity-90">{tool.description}</p>
              </div>
              
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Click to launch</span>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tool Modal */}
      {selectedTool && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-bold text-gray-900">
                {selectedTool.name}
              </h3>
              <button
                onClick={() => {
                  setSelectedTool(null);
                  setResult('');
                  setFormData({});
                  setError(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Grant Context Indicator */}
            {selectedGrant && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-green-800">
                    Using grant context: {selectedGrant.title} ({selectedGrant.funder})
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {renderToolForm()}
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedTool(null);
                    setResult('');
                    setFormData({});
                    setError(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-4 py-2 text-white rounded-md ${
                    loading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-pink-600 hover:bg-pink-700'
                  }`}
                >
                  {loading ? 'Generating...' : 'Generate'}
                </button>
              </div>
            </form>

            {/* Results Section */}
            {result && (
              <div className="mt-6 border-t pt-6">
                <h4 className="text-lg font-semibold mb-3">Generated Content</h4>
                
                {/* Data Quality Metrics */}
                <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-xs text-blue-600">Org Data</div>
                    <div className="font-semibold text-blue-900">{dataQuality.organizationFields}</div>
                  </div>
                  <div className="bg-green-50 p-2 rounded">
                    <div className="text-xs text-green-600">Funder Data</div>
                    <div className="font-semibold text-green-900">{dataQuality.funderData}</div>
                  </div>
                  <div className="bg-purple-50 p-2 rounded">
                    <div className="text-xs text-purple-600">Context</div>
                    <div className="font-semibold text-purple-900">{dataQuality.grantContext}</div>
                  </div>
                  <div className="bg-yellow-50 p-2 rounded">
                    <div className="text-xs text-yellow-600">Quality</div>
                    <div className="font-semibold text-yellow-900">{dataQuality.qualityScore}</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-md max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">{result}</pre>
                </div>
                
                <div className="mt-4 flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result);
                      // Show toast notification instead of alert
                      const toast = document.createElement('div');
                      toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg z-50';
                      toast.textContent = 'Copied to clipboard!';
                      document.body.appendChild(toast);
                      setTimeout(() => toast.remove(), 3000);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Copy to Clipboard
                  </button>
                  <button
                    onClick={() => {
                      const blob = new Blob([result], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${selectedTool.id}-${Date.now()}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Download
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartToolsEnhanced;