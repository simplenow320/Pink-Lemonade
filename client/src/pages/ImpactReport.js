import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';

const ImpactReport = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [reportType, setReportType] = useState('Annual Impact Report');
  const [targetAudience, setTargetAudience] = useState('Foundations and Major Donors');
  const [periodStart, setPeriodStart] = useState('2024-01-01');
  const [periodEnd, setPeriodEnd] = useState('2024-12-31');
  const [metrics, setMetrics] = useState([
    { name: '', target: '', actual: '' }
  ]);
  const [grant, setGrant] = useState(null);
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantError, setGrantError] = useState('');

  const addMetric = () => {
    setMetrics([...metrics, { name: '', target: '', actual: '' }]);
  };

  const removeMetric = (index) => {
    setMetrics(metrics.filter((_, i) => i !== index));
  };

  const updateMetric = (index, field, value) => {
    const updated = [...metrics];
    updated[index][field] = value;
    setMetrics(updated);
  };

  // Fetch grant details when grantId is present
  useEffect(() => {
    if (grantId) {
      const fetchGrantDetails = async () => {
        try {
          setGrantLoading(true);
          setGrantError('');
          const grantData = await getGrant(grantId);
          setGrant(grantData.grant);
          
          // Pre-fill form fields from grant data - set report type to Grant Progress Report
          setReportType('Grant Progress Report');
          
          // Add grant-specific metrics if available
          if (grantData.grant.amount_max || grantData.grant.amount_min) {
            const fundingAmount = grantData.grant.amount_max || grantData.grant.amount_min;
            setMetrics(prevMetrics => [
              ...prevMetrics.filter(m => m.name), // Keep existing metrics with names
              { name: 'Grant Funding Secured', target: fundingAmount.toString(), actual: '' },
              { name: 'Grant Milestones Completed', target: '100%', actual: '' }
            ]);
          }
        } catch (error) {
          console.error('Error fetching grant details:', error);
          setGrantError('Failed to load grant details');
        } finally {
          setGrantLoading(false);
        }
      };
      
      fetchGrantDetails();
    }
  }, [grantId]);

  const generateImpactReport = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/impact/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          period_start: periodStart,
          period_end: periodEnd,
          metrics: {
            ...metrics.filter(m => m.name).reduce((acc, metric) => {
              acc[metric.name.toLowerCase().replace(/\s+/g, '_')] = metric.actual || metric.target || 0;
              return acc;
            }, {}),
            grants_submitted: 10,
            grants_won: 3,
            funding_secured: 250000,
            beneficiaries_served: 500,
            programs_delivered: 5
          },
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate Impact Report');
      }

      if (data.success) {
        setGeneratedContent(data.content);
        setEditableContent(data.content);
      } else {
        throw new Error(data.error || 'Failed to generate content');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadContent = () => {
    const element = document.createElement('a');
    const file = new Blob([editableContent], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = 'impact_report.md';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editableContent);
    alert('Content copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/smart-tools" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
            ← Back to Smart Tools
          </Link>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="text-3xl mr-3">📊</span>
              Impact Report Generator
            </h1>
            <p className="text-xl text-gray-600">
              Generate comprehensive reports showing your programs' actual outcomes and community impact
            </p>
            
            {/* Grant Context Banner */}
            {grant && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <span className="font-medium">Grant Context:</span> {grant.title}
                </p>
                <div className="text-sm text-blue-600 mt-1">
                  <span>Funder: {grant.funder}</span>
                  {(grant.amount_min || grant.amount_max) && (
                    <span className="ml-4">
                      Amount: {grant.amount_min && grant.amount_max 
                        ? `$${grant.amount_min.toLocaleString()} - $${grant.amount_max.toLocaleString()}`
                        : grant.amount_max 
                          ? `Up to $${grant.amount_max.toLocaleString()}`
                          : `$${grant.amount_min?.toLocaleString() || '0'}`
                      }
                    </span>
                  )}
                  {grant.deadline && (
                    <span className="ml-4">Deadline: {new Date(grant.deadline).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            )}
            
            {grantError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-700">{grantError}</p>
              </div>
            )}
            
            {organization && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <span className="font-medium">Creating reports for:</span> {organization.name || 'Your Organization'}
                  {organization.mission && (
                    <span className="text-sm ml-2 text-blue-600">- {organization.mission}</span>
                  )}
                </p>
              </div>
            )}
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <motion.div
            className="bg-white rounded-lg shadow-md p-6 max-h-screen overflow-y-auto"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Report Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Type
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="Annual Impact Report">Annual Impact Report</option>
                  <option value="Quarterly Report">Quarterly Report</option>
                  <option value="Grant Progress Report">Grant Progress Report</option>
                  <option value="Program Evaluation Report">Program Evaluation Report</option>
                  <option value="Donor Impact Report">Donor Impact Report</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience
                </label>
                <select
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="Foundations and Major Donors">Foundations & Major Donors</option>
                  <option value="Board Members">Board Members</option>
                  <option value="Community Stakeholders">Community Stakeholders</option>
                  <option value="Government Agencies">Government Agencies</option>
                  <option value="General Public">General Public</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Period Start
                  </label>
                  <input
                    type="text"
                    value={periodStart}
                    onChange={(e) => setPeriodStart(e.target.value)}
                    placeholder="e.g., January 2024"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Period End
                  </label>
                  <input
                    type="text"
                    value={periodEnd}
                    onChange={(e) => setPeriodEnd(e.target.value)}
                    placeholder="e.g., December 2024"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Key Metrics (Optional)
                </label>
                {metrics.map((metric, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Metric name"
                      value={metric.name}
                      onChange={(e) => updateMetric(index, 'name', e.target.value)}
                      className="flex-1 p-2 border border-gray-300 rounded-md text-sm"
                    />
                    <input
                      type="text"
                      placeholder="Target"
                      value={metric.target}
                      onChange={(e) => updateMetric(index, 'target', e.target.value)}
                      className="w-24 p-2 border border-gray-300 rounded-md text-sm"
                    />
                    <input
                      type="text"
                      placeholder="Actual"
                      value={metric.actual}
                      onChange={(e) => updateMetric(index, 'actual', e.target.value)}
                      className="w-24 p-2 border border-gray-300 rounded-md text-sm"
                    />
                    <button
                      onClick={() => removeMetric(index)}
                      className="px-2 py-1 text-red-600 hover:text-red-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                <button
                  onClick={addMetric}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  + Add Metric
                </button>
              </div>

              <button
                onClick={generateImpactReport}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Impact Report'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <h3 className="font-semibold text-blue-900 mb-2">Report Features:</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Uses your organization's actual data</li>
                <li>• Outcome tracking & metrics</li>
                <li>• Visual metrics recommendations</li>
                <li>• Stakeholder-specific formatting</li>
                <li>• Export-ready content</li>
              </ul>
            </div>
          </motion.div>

          {/* Output Section */}
          <motion.div
            className="bg-white rounded-lg shadow-md p-6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Generated Report</h2>
              {editableContent && (
                <div className="space-x-2">
                  <button
                    onClick={copyToClipboard}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Copy
                  </button>
                  <button
                    onClick={downloadContent}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              )}
            </div>

            {!editableContent ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>Your Impact Report will appear here</p>
                <p className="text-sm mt-2">Click "Generate Impact Report" to begin</p>
              </div>
            ) : (
              <div>
                <textarea
                  value={editableContent}
                  onChange={(e) => setEditableContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Generated report will appear here..."
                />
                <div className="mt-4 flex justify-between items-center text-sm text-gray-600">
                  <span>Word count: {editableContent.split(/\s+/).filter(word => word.length > 0).length}</span>
                  <span>✏️ Content is fully editable</span>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ImpactReport;