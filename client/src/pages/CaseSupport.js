import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';
import UseInApplicationModal from '../components/ui/UseInApplicationModal';
import TemplateSelectionModal from '../components/ui/TemplateSelectionModal';
import SaveTemplateModal from '../components/ui/SaveTemplateModal';

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
  
  // Use in Application modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  
  // Template functionality state
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [isSaveTemplateModalOpen, setIsSaveTemplateModalOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateTags, setTemplateTags] = useState([]);
  const [savingTemplate, setSavingTemplate] = useState(false);

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
    if (organization && !grantId) {
      // Auto-fill campaign purpose from mission if not already set
      if (!campaignPurpose && organization.mission) {
        setCampaignPurpose(`Support our mission: ${organization.mission}`);
      }
      
      // Auto-fill campaign goal based on annual budget range if not already set
      if (!campaignGoal && organization.annual_budget_range) {
        // Extract amount from budget range string (e.g., "$100,000-$500,000" -> "250000")
        const budgetRange = organization.annual_budget_range;
        if (budgetRange.includes('-')) {
          const amounts = budgetRange.match(/\d+/g);
          if (amounts && amounts.length >= 2) {
            // Use 20% of the midpoint as a reasonable campaign goal
            const midpoint = (parseInt(amounts[0]) + parseInt(amounts[1])) / 2;
            setCampaignGoal(Math.round(midpoint * 0.2).toString());
          }
        } else if (budgetRange.includes('Over')) {
          const amount = budgetRange.match(/\d+/g)?.[0];
          if (amount) {
            // Use 10% of the minimum for "Over" ranges
            setCampaignGoal(Math.round(parseInt(amount) * 0.1).toString());
          }
        } else if (budgetRange.includes('Under')) {
          const amount = budgetRange.match(/\d+/g)?.[0];
          if (amount) {
            // Use 20% of the maximum for "Under" ranges
            setCampaignGoal(Math.round(parseInt(amount) * 0.2).toString());
          }
        }
      }
      
      // Auto-fill target donors based on demographics and focus areas
      if (!targetDonors || targetDonors === 'foundations and individual donors') {
        const donors = [];
        
        // Add foundation focus if they have established programs
        if (organization.primary_focus_areas?.length > 0) {
          const focusAreasText = organization.primary_focus_areas.slice(0, 2).join(' and ').toLowerCase();
          donors.push(`foundations focused on ${focusAreasText}`);
        }
        
        // Add demographic-specific funders if applicable
        if (organization.target_demographics?.length > 0) {
          const demographics = organization.target_demographics.slice(0, 2).join(' and ').toLowerCase();
          donors.push(`funders supporting ${demographics} communities`);
        }
        
        // Add geographic funders
        if (organization.primary_city && organization.primary_state) {
          donors.push(`local ${organization.primary_city}, ${organization.primary_state} philanthropists`);
        }
        
        // Always include individual donors
        donors.push('individual major donors');
        
        if (donors.length > 1) {
          // Only update if we have more than just "individual major donors"
          setTargetDonors(donors.join(', '));
        }
      }
    }
  }, [organization, grantId]);

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

  const handleUseInApplication = () => {
    if (!grantId) {
      alert('Grant ID is required to save content to application');
      return;
    }
    setIsModalOpen(true);
  };

  const handleModalSuccess = (data) => {
    setSuccessMessage(
      `Content saved successfully! ` +
      `<a href="${data.deep_link}" class="underline text-blue-600 hover:text-blue-800">View Application</a>`
    );
    // Clear success message after 10 seconds
    setTimeout(() => setSuccessMessage(''), 10000);
  };

  // Template handling functions
  const handleTemplateSelect = (template) => {
    if (template.parameters) {
      // Prefill form with template parameters
      setCampaignGoal(template.parameters.campaign_goal || '');
      setCampaignPurpose(template.parameters.campaign_purpose || '');
      setTimeline(template.parameters.timeline || '12 months');
      setTargetDonors(template.parameters.target_donors || 'foundations and individual donors');
    }
    
    alert(`Template "${template.name}" loaded successfully! Form has been prefilled with template parameters.`);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      alert('Please enter a template name');
      return;
    }

    if (!editableContent) {
      alert('No content available to save as template');
      return;
    }

    if (!organization?.id) {
      alert('Organization information is required to save templates');
      return;
    }

    setSavingTemplate(true);

    try {
      const inputParameters = {
        campaign_goal: campaignGoal,
        campaign_purpose: campaignPurpose,
        timeline,
        target_donors: targetDonors
      };

      const response = await fetch('/api/templates/from-smart-tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_type: 'case_support',
          name: templateName,
          description: templateDescription,
          generated_content: editableContent,
          input_parameters: inputParameters,
          organization_id: organization.id,
          tags: templateTags,
          focus_areas: organization.focus_areas || [],
          funder_types: [grant?.type || 'foundation'],
          is_shared: false
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to save template');
      }

      if (data.success) {
        setIsSaveTemplateModalOpen(false);
        setTemplateName('');
        setTemplateDescription('');
        setTemplateTags([]);
        alert('Template saved successfully!');
      } else {
        throw new Error(data.error || 'Failed to save template');
      }
    } catch (err) {
      alert(`Error saving template: ${err.message}`);
    } finally {
      setSavingTemplate(false);
    }
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
                  {grantId && (
                    <button
                      onClick={handleUseInApplication}
                      className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      Use in Application
                    </button>
                  )}
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

        {/* Success Message */}
        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md"
          >
            <div 
              className="text-green-800"
              dangerouslySetInnerHTML={{ __html: successMessage }}
            />
          </motion.div>
        )}
      </div>

      {/* Use in Application Modal */}
      <UseInApplicationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        content={editableContent}
        sourceTool="case_support"
        grantId={grantId}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
};

export default CaseSupport;