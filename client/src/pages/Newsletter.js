import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';
import TemplateSelectionModal from '../components/ui/TemplateSelectionModal';
import SaveTemplateModal from '../components/ui/SaveTemplateModal';

const Newsletter = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [theme, setTheme] = useState('');
  const [monthYear, setMonthYear] = useState('');
  const [focusArea, setFocusArea] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [grant, setGrant] = useState(null);
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantError, setGrantError] = useState('');
  
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
          
          // Pre-fill form fields with grant-specific content
          setTheme('Grant Announcement');
          setFocusArea('Grant announcement and funding success');
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

  const generateNewsletter = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/newsletter/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme: theme || 'Community Impact',
          month_year: monthYear || new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
          focus_area: focusArea || 'General updates and achievements',
          target_audience: targetAudience || 'General stakeholders',
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate Newsletter');
      }

      setGeneratedContent(data.content);
      setEditableContent(data.content);
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
    element.download = 'newsletter_content.md';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editableContent);
    alert('Content copied to clipboard!');
  };

  // Template handling functions
  const handleTemplateSelect = (template) => {
    if (template.parameters) {
      // Prefill form with template parameters
      setTheme(template.parameters.theme || '');
      setMonthYear(template.parameters.month_year || '');
      setFocusArea(template.parameters.focus_area || '');
      setTargetAudience(template.parameters.target_audience || '');
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
        theme,
        month_year: monthYear,
        focus_area: focusArea,
        target_audience: targetAudience
      };

      const response = await fetch('/api/templates/from-smart-tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_type: 'newsletter',
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

  // Newsletter theme options
  const themeOptions = [
    'Community Impact',
    'Program Updates',
    'Success Stories',
    'Seasonal Updates',
    'Fundraising Focus',
    'Volunteer Spotlight',
    'Partnership Highlights',
    'Annual Review'
  ];

  // Focus area options
  const focusAreaOptions = [
    'General updates and achievements',
    'Program outcomes and success metrics',
    'Community stories and testimonials',
    'Upcoming events and opportunities',
    'Financial transparency and impact',
    'Staff and volunteer recognition',
    'Partnership and collaboration news',
    'Advocacy and policy updates'
  ];

  // Target audience options
  const audienceOptions = [
    'General stakeholders',
    'Major donors and foundations',
    'Community members and beneficiaries',
    'Volunteers and supporters',
    'Board members and leadership',
    'Partner organizations',
    'Media and press contacts',
    'Government and policy makers'
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/smart-tools" className="text-purple-600 hover:text-purple-700 mb-4 inline-block">
            ← Back to Smart Tools
          </Link>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="text-3xl mr-3">📰</span>
              Newsletter Generator
            </h1>
            <p className="text-xl text-gray-600">
              AI-powered newsletter content creation for stakeholder communication and engagement
            </p>
            
            {/* Grant Context Banner */}
            {grant && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <span className="font-medium">Grant Context:</span> {grant.title}
                </p>
                <div className="text-sm text-blue-600 mt-1">
                  <span>Funder: {grant.funder}</span>
                  <span className="ml-4">Creating newsletter to announce this grant</span>
                </div>
              </div>
            )}
            
            {grantError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-700">{grantError}</p>
              </div>
            )}
            
            {organization && (
              <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-md">
                <p className="text-purple-800">
                  <span className="font-medium">Creating newsletters for:</span> {organization.name || 'Your Organization'}
                  {organization.mission && (
                    <span className="text-sm ml-2 text-purple-600">- {organization.mission}</span>
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
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Newsletter Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Newsletter Theme
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Select a theme...</option>
                  {themeOptions.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Month & Year
                </label>
                <input
                  type="text"
                  value={monthYear}
                  onChange={(e) => setMonthYear(e.target.value)}
                  placeholder="e.g., September 2025, Q3 2025, Fall 2025"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Focus Area
                </label>
                <select
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Select focus area...</option>
                  {focusAreaOptions.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience
                </label>
                <select
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Select target audience...</option>
                  {audienceOptions.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={generateNewsletter}
                disabled={loading}
                className="w-full bg-purple-600 text-white py-3 px-4 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Newsletter Content'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-md">
              <h3 className="font-semibold text-purple-900 mb-2">What you'll get:</h3>
              <ul className="text-sm text-purple-800 space-y-1">
                <li>• Professional newsletter content structure</li>
                <li>• Audience-appropriate tone and messaging</li>
                <li>• Section headers and content blocks</li>
                <li>• Call-to-action suggestions</li>
                <li>• Email-ready formatting</li>
                <li>• Print-friendly layout options</li>
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
              <h2 className="text-2xl font-semibold text-gray-900">Generated Newsletter</h2>
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
                    className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              )}
            </div>

            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                <span className="ml-3 text-gray-600">Generating newsletter content...</span>
              </div>
            )}

            {editableContent && !loading && (
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg border">
                  <h3 className="font-medium text-gray-900 mb-2">Content Preview</h3>
                  <div className="max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {editableContent.substring(0, 500)}
                      {editableContent.length > 500 && '...'}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Edit Content
                  </label>
                  <textarea
                    value={editableContent}
                    onChange={(e) => setEditableContent(e.target.value)}
                    className="w-full h-64 p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-sm font-mono"
                    placeholder="Generated newsletter content will appear here..."
                  />
                </div>
              </div>
            )}

            {!editableContent && !loading && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📰</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Create</h3>
                <p className="text-gray-600">
                  Fill in the newsletter details and click generate to create your comprehensive newsletter content.
                </p>
              </div>
            )}
          </motion.div>
        </div>

        {/* Additional Features Section */}
        {editableContent && (
          <motion.div
            className="mt-8 bg-white rounded-lg shadow-md p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Newsletter Sections</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">📬 Header & Welcome</h4>
                <p className="text-sm text-purple-700">Professional header with warm welcome message</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">🎯 Main Content</h4>
                <p className="text-sm text-purple-700">Core message and key updates for your audience</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">📊 Impact Highlights</h4>
                <p className="text-sm text-purple-700">Key achievements and success metrics</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">📅 Upcoming Events</h4>
                <p className="text-sm text-purple-700">Important dates and opportunities</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">🤝 Call to Action</h4>
                <p className="text-sm text-purple-700">Clear next steps for reader engagement</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 mb-2">📝 Footer</h4>
                <p className="text-sm text-purple-700">Contact info and social media links</p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Newsletter;