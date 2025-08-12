import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SmartToolsEnhanced = ({ toolType, onClose }) => {
  const [grants, setGrants] = useState([]);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [dataQuality, setDataQuality] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch available grants for context
    const fetchGrants = async () => {
      try {
        const response = await fetch('/api/grants/list');
        if (response.ok) {
          const data = await response.json();
          setGrants(data.grants || []);
        }
      } catch (error) {
        console.error('Error fetching grants:', error);
      }
    };
    fetchGrants();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Prepare enhanced request with grant context
      const requestData = {
        ...formData,
        grant_id: selectedGrant?.id || null,
        tool_type: toolType
      };

      // Determine endpoint based on tool type
      let endpoint = '';
      switch (toolType) {
        case 'case-support':
          endpoint = '/api/writing/case-support';
          break;
        case 'grant-pitch':
          endpoint = '/api/writing/grant-pitch';
          break;
        case 'impact-report':
          endpoint = '/api/writing/impact-report';
          break;
        case 'writing-assistant':
          endpoint = '/api/writing/improve';
          requestData.improvement_type = formData.improvement_type || 'strategic';
          break;
        default:
          endpoint = '/api/writing/improve';
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();
      
      if (data.success) {
        setResult(data.content || data.improved_text);
        
        // Set data quality indicators
        setDataQuality({
          organizationFields: data.data_sources?.organization_fields_used || 'All available',
          funderData: data.data_sources?.authentic_funder_data ? 'Verified' : 'Not available',
          grantContext: data.data_sources?.grant_context_included ? 'Included' : 'Not included',
          qualityScore: data.quality_indicators?.industry_leading_quality ? '⭐⭐⭐⭐⭐' : '⭐⭐⭐'
        });
      } else {
        setResult('Error generating content. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      setResult('Error generating content. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const getToolTitle = () => {
    switch (toolType) {
      case 'case-support':
        return 'Enhanced Case for Support Generator';
      case 'grant-pitch':
        return 'Strategic Grant Pitch Builder';
      case 'impact-report':
        return 'Comprehensive Impact Report';
      case 'writing-assistant':
        return 'AI Writing Enhancement';
      default:
        return 'Smart Tool';
    }
  };

  const renderToolForm = () => {
    switch (toolType) {
      case 'case-support':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Grant for Context (Optional)
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                onChange={(e) => {
                  const grant = grants.find(g => g.id === parseInt(e.target.value));
                  setSelectedGrant(grant);
                }}
              >
                <option value="">No specific grant (general case)</option>
                {grants.map(grant => (
                  <option key={grant.id} value={grant.id}>
                    {grant.title} - {grant.funder}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Financial Need
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="e.g., $50,000 for youth programs"
                onChange={(e) => setFormData({...formData, financial_need: e.target.value})}
              />
            </div>
          </>
        );
      
      case 'grant-pitch':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Grant for Pitch
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                onChange={(e) => {
                  const grant = grants.find(g => g.id === parseInt(e.target.value));
                  setSelectedGrant(grant);
                  setFormData({...formData, funder_name: grant?.funder || ''});
                }}
              >
                <option value="">Select a grant</option>
                {grants.map(grant => (
                  <option key={grant.id} value={grant.id}>
                    {grant.title} - {grant.funder}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Funder Name
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                value={formData.funder_name || selectedGrant?.funder || ''}
                onChange={(e) => setFormData({...formData, funder_name: e.target.value})}
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alignment Areas
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="e.g., Youth development, education"
                onChange={(e) => setFormData({...formData, alignment: e.target.value})}
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Funding Amount
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="e.g., $25,000"
                onChange={(e) => setFormData({...formData, funding_amount: e.target.value})}
              />
            </div>
          </>
        );
      
      case 'impact-report':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grant to Report On (Optional)
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                onChange={(e) => {
                  const grant = grants.find(g => g.id === parseInt(e.target.value));
                  setSelectedGrant(grant);
                }}
              >
                <option value="">General organizational impact</option>
                {grants.map(grant => (
                  <option key={grant.id} value={grant.id}>
                    {grant.title} - {grant.funder}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Period
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  className="px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="Start: Jan 2024"
                  onChange={(e) => setFormData({...formData, period_start: e.target.value})}
                />
                <input
                  type="text"
                  className="px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="End: Dec 2024"
                  onChange={(e) => setFormData({...formData, period_end: e.target.value})}
                />
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Programs to Include
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows="2"
                placeholder="e.g., Youth mentorship, After-school programs"
                onChange={(e) => setFormData({...formData, programs_covered: e.target.value})}
              />
            </div>
          </>
        );
      
      case 'writing-assistant':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grant Context (Optional)
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                onChange={(e) => {
                  const grant = grants.find(g => g.id === parseInt(e.target.value));
                  setSelectedGrant(grant);
                }}
              >
                <option value="">No specific grant</option>
                {grants.map(grant => (
                  <option key={grant.id} value={grant.id}>
                    {grant.title} - {grant.funder}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Improvement Type
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                onChange={(e) => setFormData({...formData, improvement_type: e.target.value})}
              >
                <option value="strategic">Strategic Enhancement</option>
                <option value="clarity">Improve Clarity</option>
                <option value="persuasive">Make More Persuasive</option>
                <option value="concise">Make More Concise</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text to Improve
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows="4"
                placeholder="Paste your grant text here..."
                onChange={(e) => setFormData({...formData, text: e.target.value})}
                required
              />
            </div>
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-2xl font-bold text-gray-900">
            {getToolTitle()}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Data Quality Indicator */}
        {selectedGrant && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-green-800">
                Enhanced mode: Using grant context for {selectedGrant.funder}
              </span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {renderToolForm()}
          
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-pink-600 text-white rounded-md hover:bg-pink-700 disabled:opacity-50"
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
            {dataQuality.organizationFields && (
              <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-blue-50 p-2 rounded">
                  <div className="text-xs text-blue-600">Org Fields Used</div>
                  <div className="font-semibold text-blue-900">{dataQuality.organizationFields}</div>
                </div>
                <div className="bg-green-50 p-2 rounded">
                  <div className="text-xs text-green-600">Funder Data</div>
                  <div className="font-semibold text-green-900">{dataQuality.funderData}</div>
                </div>
                <div className="bg-purple-50 p-2 rounded">
                  <div className="text-xs text-purple-600">Grant Context</div>
                  <div className="font-semibold text-purple-900">{dataQuality.grantContext}</div>
                </div>
                <div className="bg-yellow-50 p-2 rounded">
                  <div className="text-xs text-yellow-600">Quality Score</div>
                  <div className="font-semibold text-yellow-900">{dataQuality.qualityScore}</div>
                </div>
              </div>
            )}
            
            <div className="bg-gray-50 p-4 rounded-md max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm">{result}</pre>
            </div>
            
            <div className="mt-4 flex justify-end space-x-3">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result);
                  alert('Content copied to clipboard!');
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
                  a.download = `${toolType}-${Date.now()}.txt`;
                  a.click();
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
  );
};

export default SmartToolsEnhanced;