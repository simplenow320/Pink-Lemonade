import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';

const GrantPitch = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [funderName, setFunderName] = useState('');
  const [alignment, setAlignment] = useState('');
  const [fundingNeed, setFundingNeed] = useState('');
  const [fundingAmount, setFundingAmount] = useState('');
  const [pitchType, setPitchType] = useState('elevator');
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
          if (grantData.grant.funder) {
            setFunderName(grantData.grant.funder);
          }
          if (grantData.grant.amount_min || grantData.grant.amount_max) {
            const amountRange = grantData.grant.amount_min && grantData.grant.amount_max 
              ? `$${grantData.grant.amount_min.toLocaleString()} - $${grantData.grant.amount_max.toLocaleString()}`
              : grantData.grant.amount_max 
                ? `Up to $${grantData.grant.amount_max.toLocaleString()}`
                : `$${grantData.grant.amount_min?.toLocaleString() || '0'}`;
            setFundingAmount(amountRange);
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
    if (organization && !alignment && !fundingNeed) {
      if (organization.mission) {
        setAlignment(`Our mission: ${organization.mission}`);
      }
      if (organization.focus_areas) {
        setFundingNeed(`Support for our ${organization.focus_areas} programs`);
      }
    }
  }, [organization, alignment, fundingNeed]);

  const generateGrantPitch = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/pitch/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pitch_type: pitchType,
          funder_name: funderName || 'Potential Funder',
          alignment: alignment || 'Mission alignment and shared values',
          funding_need: fundingNeed || 'General operating support',
          funding_amount: fundingAmount || 'Not specified',
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate Grant Pitch');
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
    element.download = 'grant_pitch.md';
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
          <Link to="/smart-tools" className="text-green-600 hover:text-green-700 mb-4 inline-block">
            ← Back to Smart Tools
          </Link>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="text-3xl mr-3">🎯</span>
              Grant Pitch Generator
            </h1>
            <p className="text-xl text-gray-600">
              AI-powered pitch generator for presentations, emails, and verbal delivery to funders
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
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-green-800">
                  <span className="font-medium">Creating pitches for:</span> {organization.name || 'Your Organization'}
                  {organization.mission && (
                    <span className="text-sm ml-2 text-green-600">- {organization.mission}</span>
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
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Pitch Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funder Name
                </label>
                <input
                  type="text"
                  value={funderName}
                  onChange={(e) => setFunderName(e.target.value)}
                  placeholder="e.g., Ford Foundation, Gates Foundation"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alignment Areas
                </label>
                <textarea
                  value={alignment}
                  onChange={(e) => setAlignment(e.target.value)}
                  placeholder="How does your work align with this funder's priorities?"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  rows="2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funding Need
                </label>
                <textarea
                  value={fundingNeed}
                  onChange={(e) => setFundingNeed(e.target.value)}
                  placeholder="What will the funding be used for?"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  rows="2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funding Amount
                </label>
                <input
                  type="text"
                  value={fundingAmount}
                  onChange={(e) => setFundingAmount(e.target.value)}
                  placeholder="e.g., $50,000, $100,000-$250,000"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pitch Type
                </label>
                <select
                  value={pitchType}
                  onChange={(e) => setPitchType(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                >
                  <option value="elevator">Elevator Pitch (30-60 seconds)</option>
                  <option value="executive">Executive Summary (2-3 minutes)</option>
                  <option value="detailed">Detailed Presentation (5-10 minutes)</option>
                </select>
              </div>

              <button
                onClick={generateGrantPitch}
                disabled={loading}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Grant Pitch'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <h3 className="font-semibold text-green-900 mb-2">What you'll get:</h3>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• One-Page Pitch (formatted document)</li>
                <li>• Email Pitch (subject line + body)</li>
                <li>• Verbal Script (60-90 seconds)</li>
                <li>• Funder-specific customization</li>
                <li>• Multiple format options</li>
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
              <h2 className="text-2xl font-semibold text-gray-900">Generated Pitches</h2>
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
                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              )}
            </div>

            {!editableContent ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                </svg>
                <p>Your grant pitches will appear here</p>
                <p className="text-sm mt-2">Click "Generate Grant Pitch" to create three formats</p>
              </div>
            ) : (
              <div>
                <textarea
                  value={editableContent}
                  onChange={(e) => setEditableContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm focus:ring-green-500 focus:border-green-500"
                  placeholder="Generated pitches will appear here..."
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

export default GrantPitch;