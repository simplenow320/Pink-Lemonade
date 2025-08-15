import React, { useState, useEffect } from 'react';

const Phase4AIWriter = () => {
  const [activeTab, setActiveTab] = useState('narrative');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [templates, setTemplates] = useState({});
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [grants, setGrants] = useState([]);
  
  // Form states
  const [narrativeType, setNarrativeType] = useState('mission_alignment');
  const [maxWords, setMaxWords] = useState(250);
  const [optimizationType, setOptimizationType] = useState('clarity');
  const [contentToOptimize, setContentToOptimize] = useState('');
  const [budgetData, setBudgetData] = useState({
    total: 50000,
    categories: {
      'Personnel': 25000,
      'Equipment': 10000,
      'Operations': 10000,
      'Indirect': 5000
    }
  });
  const [impactData, setImpactData] = useState({
    beneficiaries: '500 community members',
    timeline: '12 months',
    outcomes: ['Increased access to services', 'Improved health outcomes'],
    metrics: ['Number served', 'Health indicators']
  });

  useEffect(() => {
    fetchGrants();
    fetchTemplates();
  }, []);

  const fetchGrants = async () => {
    try {
      const response = await fetch('/api/phase2/applications/staged');
      const data = await response.json();
      if (data.success) {
        setGrants(data.grants || []);
        if (data.grants && data.grants.length > 0) {
          setSelectedGrant(data.grants[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching grants:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/phase4/writer/templates');
      const data = await response.json();
      if (data.success) {
        setTemplates(data.templates || {});
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const generateNarrative = async () => {
    if (!selectedGrant) {
      alert('Please select a grant first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/phase4/writer/narrative', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_id: selectedGrant.id,
          narrative_type: narrativeType
        })
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedContent(data.narrative);
      } else {
        alert(data.error || 'Failed to generate narrative');
      }
    } catch (error) {
      console.error('Error generating narrative:', error);
      alert('Error generating narrative');
    } finally {
      setLoading(false);
    }
  };

  const generateExecutiveSummary = async () => {
    if (!selectedGrant) {
      alert('Please select a grant first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/phase4/writer/executive-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_id: selectedGrant.id,
          max_words: maxWords
        })
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedContent(data.executive_summary);
      } else {
        alert(data.error || 'Failed to generate executive summary');
      }
    } catch (error) {
      console.error('Error generating executive summary:', error);
      alert('Error generating executive summary');
    } finally {
      setLoading(false);
    }
  };

  const generateImpactStatement = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/phase4/writer/impact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(impactData)
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedContent(data.impact_statement);
      } else {
        alert(data.error || 'Failed to generate impact statement');
      }
    } catch (error) {
      console.error('Error generating impact statement:', error);
      alert('Error generating impact statement');
    } finally {
      setLoading(false);
    }
  };

  const generateBudgetNarrative = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/phase4/writer/budget-narrative', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(budgetData)
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedContent(data.budget_narrative);
      } else {
        alert(data.error || 'Failed to generate budget narrative');
      }
    } catch (error) {
      console.error('Error generating budget narrative:', error);
      alert('Error generating budget narrative');
    } finally {
      setLoading(false);
    }
  };

  const optimizeContent = async () => {
    if (!contentToOptimize) {
      alert('Please enter content to optimize');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/phase4/writer/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: contentToOptimize,
          optimization_type: optimizationType,
          target: optimizationType === 'length' ? maxWords : optimizationType === 'tone' ? 'professional' : null
        })
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedContent(data.optimized);
      } else {
        alert(data.error || 'Failed to optimize content');
      }
    } catch (error) {
      console.error('Error optimizing content:', error);
      alert('Error optimizing content');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedContent);
    alert('Content copied to clipboard!');
  };

  const renderNarrativeGenerator = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Grant
        </label>
        <select
          value={selectedGrant?.id || ''}
          onChange={(e) => setSelectedGrant(grants.find(g => g.id === parseInt(e.target.value)))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        >
          <option value="">Select a grant...</option>
          {grants.map(grant => (
            <option key={grant.id} value={grant.id}>
              {grant.title || grant.grant_name} - {grant.funding_organization || grant.funder}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Narrative Type
        </label>
        <select
          value={narrativeType}
          onChange={(e) => setNarrativeType(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        >
          <option value="mission_alignment">Mission Alignment</option>
          <option value="need_statement">Need Statement</option>
          <option value="impact">Impact Statement</option>
          <option value="sustainability">Sustainability Plan</option>
          <option value="budget">Budget Narrative</option>
        </select>
      </div>

      <button
        onClick={generateNarrative}
        disabled={loading || !selectedGrant}
        className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
      >
        {loading ? 'Generating...' : 'Generate Narrative'}
      </button>
    </div>
  );

  const renderExecutiveSummary = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Grant
        </label>
        <select
          value={selectedGrant?.id || ''}
          onChange={(e) => setSelectedGrant(grants.find(g => g.id === parseInt(e.target.value)))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        >
          <option value="">Select a grant...</option>
          {grants.map(grant => (
            <option key={grant.id} value={grant.id}>
              {grant.title || grant.grant_name} - {grant.funding_organization || grant.funder}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Maximum Words
        </label>
        <input
          type="number"
          value={maxWords}
          onChange={(e) => setMaxWords(parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        />
      </div>

      <button
        onClick={generateExecutiveSummary}
        disabled={loading || !selectedGrant}
        className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
      >
        {loading ? 'Generating...' : 'Generate Executive Summary'}
      </button>
    </div>
  );

  const renderImpactStatement = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Beneficiaries
        </label>
        <input
          type="text"
          value={impactData.beneficiaries}
          onChange={(e) => setImpactData({...impactData, beneficiaries: e.target.value})}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timeline
        </label>
        <input
          type="text"
          value={impactData.timeline}
          onChange={(e) => setImpactData({...impactData, timeline: e.target.value})}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        />
      </div>

      <button
        onClick={generateImpactStatement}
        disabled={loading}
        className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
      >
        {loading ? 'Generating...' : 'Generate Impact Statement'}
      </button>
    </div>
  );

  const renderBudgetNarrative = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Total Budget
        </label>
        <input
          type="number"
          value={budgetData.total}
          onChange={(e) => setBudgetData({...budgetData, total: parseInt(e.target.value)})}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Budget Categories (JSON)
        </label>
        <textarea
          value={JSON.stringify(budgetData.categories, null, 2)}
          onChange={(e) => {
            try {
              setBudgetData({...budgetData, categories: JSON.parse(e.target.value)});
            } catch (err) {
              // Invalid JSON, ignore
            }
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
          rows={5}
        />
      </div>

      <button
        onClick={generateBudgetNarrative}
        disabled={loading}
        className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
      >
        {loading ? 'Generating...' : 'Generate Budget Narrative'}
      </button>
    </div>
  );

  const renderOptimizer = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Content to Optimize
        </label>
        <textarea
          value={contentToOptimize}
          onChange={(e) => setContentToOptimize(e.target.value)}
          placeholder="Paste your content here..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
          rows={6}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Optimization Type
        </label>
        <select
          value={optimizationType}
          onChange={(e) => setOptimizationType(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
        >
          <option value="clarity">Improve Clarity</option>
          <option value="tone">Adjust Tone</option>
          <option value="length">Adjust Length</option>
          <option value="compliance">Check Compliance</option>
        </select>
      </div>

      {optimizationType === 'length' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Word Count
          </label>
          <input
            type="number"
            value={maxWords}
            onChange={(e) => setMaxWords(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
          />
        </div>
      )}

      <button
        onClick={optimizeContent}
        disabled={loading || !contentToOptimize}
        className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
      >
        {loading ? 'Optimizing...' : 'Optimize Content'}
      </button>
    </div>
  );

  const renderTemplates = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Available Templates</h3>
      {Object.entries(templates).map(([key, template]) => (
        <div key={key} className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 capitalize mb-2">
            {key.replace(/_/g, ' ')}
          </h4>
          <pre className="text-sm text-gray-600 whitespace-pre-wrap font-mono bg-gray-50 p-3 rounded">
            {template}
          </pre>
          <button
            onClick={() => {
              navigator.clipboard.writeText(template);
              alert('Template copied to clipboard!');
            }}
            className="mt-2 text-pink-500 hover:text-pink-600 text-sm"
          >
            Copy Template
          </button>
        </div>
      ))}
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Phase 4: AI Writing Assistant
        </h2>
        <p className="text-gray-600">
          Generate professional grant narratives, proposals, and supporting documents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Writing Tools</h3>
            <div className="space-y-2">
              <button
                onClick={() => setActiveTab('narrative')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'narrative' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Grant Narratives
              </button>
              <button
                onClick={() => setActiveTab('executive')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'executive' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Executive Summary
              </button>
              <button
                onClick={() => setActiveTab('impact')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'impact' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Impact Statement
              </button>
              <button
                onClick={() => setActiveTab('budget')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'budget' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Budget Narrative
              </button>
              <button
                onClick={() => setActiveTab('optimize')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'optimize' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Content Optimizer
              </button>
              <button
                onClick={() => setActiveTab('templates')}
                className={`w-full text-left px-3 py-2 rounded-md ${
                  activeTab === 'templates' ? 'bg-pink-100 text-pink-700' : 'hover:bg-gray-100'
                }`}
              >
                <svg className="inline-block w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                </svg>
                Templates
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            {activeTab === 'narrative' && renderNarrativeGenerator()}
            {activeTab === 'executive' && renderExecutiveSummary()}
            {activeTab === 'impact' && renderImpactStatement()}
            {activeTab === 'budget' && renderBudgetNarrative()}
            {activeTab === 'optimize' && renderOptimizer()}
            {activeTab === 'templates' && renderTemplates()}
          </div>

          {generatedContent && (
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Generated Content</h3>
                <div className="space-x-2">
                  <button
                    onClick={copyToClipboard}
                    className="text-pink-500 hover:text-pink-600 text-sm"
                  >
                    Copy to Clipboard
                  </button>
                  <span className="text-sm text-gray-500">
                    {generatedContent.split(' ').length} words
                  </span>
                </div>
              </div>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-gray-700">
                  {generatedContent}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Phase4AIWriter;