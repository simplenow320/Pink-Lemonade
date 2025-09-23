import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';
import UseInApplicationModal from '../components/ui/UseInApplicationModal';
import TemplateSelectionModal from '../components/ui/TemplateSelectionModal';
import SaveTemplateModal from '../components/ui/SaveTemplateModal';

const ThankYouLetter = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [donorName, setDonorName] = useState('');
  const [donationAmount, setDonationAmount] = useState('');
  const [donationPurpose, setDonationPurpose] = useState('');
  const [isRecurring, setIsRecurring] = useState(false);
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
          
          // Pre-fill donor name with funder name if available
          if (grantData.grant.funder) {
            setDonorName(grantData.grant.funder);
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

  const generateThankYouLetter = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/thank-you/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          donor_name: donorName || 'Valued Donor',
          donation_amount: donationAmount || 'Your generous donation',
          donation_purpose: donationPurpose || 'General operating support',
          is_recurring: isRecurring,
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate Thank You Letter');
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
    element.download = 'thank_you_letter.md';
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
      setDonorName(template.parameters.donor_name || '');
      setDonationAmount(template.parameters.donation_amount || '');
      setDonationPurpose(template.parameters.donation_purpose || '');
      setIsRecurring(template.parameters.is_recurring || false);
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
        donor_name: donorName,
        donation_amount: donationAmount,
        donation_purpose: donationPurpose,
        is_recurring: isRecurring
      };

      const response = await fetch('/api/templates/from-smart-tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_type: 'thank_you_letter',
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
              <span className="text-3xl mr-3">💝</span>
              Thank You Letter Generator
            </h1>
            <p className="text-xl text-gray-600">
              AI-powered personalized thank you letters to show appreciation for your donors' generosity
            </p>
            
            {/* Grant Context Banner */}
            {grant && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <span className="font-medium">Grant Context:</span> {grant.title}
                </p>
                <div className="text-sm text-blue-600 mt-1">
                  <span>Funder: {grant.funder}</span>
                  <span className="ml-4">Creating thank you letter for this grant award</span>
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
                  <span className="font-medium">Creating letters for:</span> {organization.name || 'Your Organization'}
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
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Donor Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Donor Name
                </label>
                <input
                  type="text"
                  value={donorName}
                  onChange={(e) => setDonorName(e.target.value)}
                  placeholder="e.g., John Smith, Smith Family Foundation"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Donation Amount
                </label>
                <input
                  type="text"
                  value={donationAmount}
                  onChange={(e) => setDonationAmount(e.target.value)}
                  placeholder="e.g., $500, $1,000, $2,500"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Donation Purpose
                </label>
                <textarea
                  value={donationPurpose}
                  onChange={(e) => setDonationPurpose(e.target.value)}
                  placeholder="What was the donation intended for? (e.g., youth programs, emergency relief, general support)"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                  rows="3"
                />
              </div>

              <div>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={isRecurring}
                    onChange={(e) => setIsRecurring(e.target.checked)}
                    className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    This is a recurring/monthly donation
                  </span>
                </label>
              </div>

              <button
                onClick={generateThankYouLetter}
                disabled={loading}
                className="w-full bg-pink-600 text-white py-3 px-4 rounded-md hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Thank You Letter'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-pink-50 border border-pink-200 rounded-md">
              <h3 className="font-semibold text-pink-900 mb-2">What you'll get:</h3>
              <ul className="text-sm text-pink-800 space-y-1">
                <li>• Personalized thank you letter</li>
                <li>• Professional tone and formatting</li>
                <li>• Donation-specific acknowledgment</li>
                <li>• Impact messaging tailored to your cause</li>
                <li>• Ready for print or email delivery</li>
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
              <h2 className="text-2xl font-semibold text-gray-900">Generated Thank You Letter</h2>
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                <p>Your personalized thank you letter will appear here</p>
                <p className="text-sm mt-2">Fill in the donor details and click "Generate Thank You Letter"</p>
              </div>
            ) : (
              <div>
                <textarea
                  value={editableContent}
                  onChange={(e) => setEditableContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm focus:ring-pink-500 focus:border-pink-500"
                  placeholder="Generated thank you letter will appear here..."
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
        sourceTool="thank_you_letter"
        grantId={grantId}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
};

export default ThankYouLetter;