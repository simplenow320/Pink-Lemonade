import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';

const CaseSupport = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [campaignGoal, setCampaignGoal] = useState('');
  const [campaignPurpose, setCampaignPurpose] = useState('');
  const [timeline, setTimeline] = useState('12 months');
  const [targetDonors, setTargetDonors] = useState('foundations and individual donors');
  const [grant, setGrant] = useState(null);
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantError, setGrantError] = useState('');

  // Fetch grant details when grantId is present
  useEffect(() => {
    if (grantId) {
      const fetchGrantDetails = async () => {
        try {
          setGrantLoading(true);
          setGrantError('');
          const grantData = await getGrant(grantId);
          setGrant(grantData.grant);
          
          // Pre-fill form fields from grant data
          if (grantData.grant.amount_max) {
            setCampaignGoal(grantData.grant.amount_max.toString());
          } else if (grantData.grant.amount_min) {
            setCampaignGoal(grantData.grant.amount_min.toString());
          }
          if (grantData.grant.title && grantData.grant.funder) {
            setCampaignPurpose(`Secure funding for: ${grantData.grant.title} from ${grantData.grant.funder}`);
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

  // Auto-populate fields from organization data
  useEffect(() => {
    if (organization && !campaignPurpose && !grantId) {
      if (organization.mission) {
        setCampaignPurpose(`Support our mission: ${organization.mission}`);
      }
    }
  }, [organization, campaignPurpose, grantId]);

  const generateCaseSupport = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/case/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          campaign_goal: campaignGoal || 100000,
          campaign_purpose: campaignPurpose || 'general support',
          timeline: timeline,
          target_donors: targetDonors,
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate Case for Support');
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
    element.download = 'case_for_support.md';
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
          <Link to="/smart-tools" className="text-pink-600 hover:text-pink-700 mb-4 inline-block">
            ← Back to Smart Tools
          </Link>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="text-3xl mr-3">📋</span>
              Case for Support Generator
            </h1>
            <p className="text-xl text-gray-600">
              Create compelling case documents that make the argument for why your organization deserves funding
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
              <div className="mt-4 p-3 bg-pink-50 border border-pink-200 rounded-md">
                <p className="text-pink-800">
                  <span className="font-medium">Creating case for:</span> {organization.name || 'Your Organization'}
                  {organization.mission && (
                    <span className="text-sm ml-2 text-pink-600">- {organization.mission}</span>
                  )}
                </p>
              </div>
            )}
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <motion.div
            className="bg-white rounded-lg shadow-md p-6"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Campaign Goal (Amount)
                </label>
                <input
                  type="number"
                  value={campaignGoal}
                  onChange={(e) => setCampaignGoal(e.target.value)}
                  placeholder="e.g., 100000, 250000, 500000"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Campaign Purpose
                </label>
                <textarea
                  value={campaignPurpose}
                  onChange={(e) => setCampaignPurpose(e.target.value)}
                  placeholder="Describe what the funding will be used for (e.g., 'To expand our after-school programs to serve 200 more students')"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                  rows="3"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timeline
                </label>
                <select
                  value={timeline}
                  onChange={(e) => setTimeline(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                >
                  <option value="6 months">6 months</option>
                  <option value="12 months">12 months</option>
                  <option value="18 months">18 months</option>
                  <option value="24 months">24 months</option>
                  <option value="36 months">36 months</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Donors
                </label>
                <select
                  value={targetDonors}
                  onChange={(e) => setTargetDonors(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                >
                  <option value="foundations and individual donors">Foundations & Individual Donors</option>
                  <option value="corporate sponsors">Corporate Sponsors</option>
                  <option value="government agencies">Government Agencies</option>
                  <option value="community foundations">Community Foundations</option>
                  <option value="faith-based funders">Faith-Based Funders</option>
                  <option value="major donors">Major Donors</option>
                </select>
              </div>

              <button
                onClick={generateCaseSupport}
                disabled={loading}
                className="w-full bg-pink-600 text-white py-3 px-4 rounded-md hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Case for Support'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-pink-50 border border-pink-200 rounded-md">
              <h3 className="font-semibold text-pink-900 mb-2">How it works:</h3>
              <ul className="text-sm text-pink-800 space-y-1">
                <li>• Uses your organization profile data</li>
                <li>• Generates professional funding documents</li>
                <li>• Creates mission-driven narratives</li>
                <li>• Produces donor-ready content</li>
                <li>• Fully editable after generation</li>
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
              <h2 className="text-2xl font-semibold text-gray-900">Generated Content</h2>
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
                    className="px-3 py-1 text-sm bg-pink-100 text-pink-700 rounded-md hover:bg-pink-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              )}
            </div>

            {!editableContent ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Your generated Case for Support will appear here</p>
                <p className="text-sm mt-2">Click "Generate Case for Support" to begin</p>
              </div>
            ) : (
              <div>
                <textarea
                  value={editableContent}
                  onChange={(e) => setEditableContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm focus:ring-pink-500 focus:border-pink-500"
                  placeholder="Generated content will appear here..."
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

export default CaseSupport;