import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import SaveTemplateModal from '../components/ui/SaveTemplateModal';
import TemplateSelectionModal from '../components/ui/TemplateSelectionModal';

const GrantApplicationBuilder = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Application sections
  const [sections, setSections] = useState({
    executiveSummary: { title: 'Executive Summary', content: '', loading: false },
    organizationBackground: { title: 'Organization Background', content: '', loading: false },
    needStatement: { title: 'Need Statement / Problem Description', content: '', loading: false },
    projectDescription: { title: 'Project Description / Approach', content: '', loading: false },
    goalsObjectives: { title: 'Goals & Objectives', content: '', loading: false },
    evaluationPlan: { title: 'Evaluation Plan', content: '', loading: false },
    budgetNarrative: { title: 'Budget Narrative', content: '', loading: false },
    sustainabilityPlan: { title: 'Sustainability Plan', content: '', loading: false },
    appendix: { title: 'Appendix / Supporting Materials', content: '', loading: false }
  });

  // Grant details (optional)
  const [grantTitle, setGrantTitle] = useState('');
  const [funderName, setFunderName] = useState('');
  const [requestAmount, setRequestAmount] = useState('');
  
  // Template functionality
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [isSaveTemplateModalOpen, setIsSaveTemplateModalOpen] = useState(false);

  // Auto-populate organization background when organization data loads
  useEffect(() => {
    if (organization && !sections.organizationBackground.content) {
      const orgBackground = `
Organization: ${organization.name || ''}
Mission: ${organization.mission || ''}
Type: ${organization.org_type || ''}
Focus Areas: ${organization.primary_focus_areas || ''}
Service Area: ${organization.service_area_type || ''}
Annual Budget: ${organization.annual_budget_range || ''}
Staff Size: ${organization.staff_size || ''}

${organization.description || ''}

History and Accomplishments:
${organization.history || ''}

Programs and Services:
${organization.programs_description || ''}
      `.trim();

      setSections(prev => ({
        ...prev,
        organizationBackground: {
          ...prev.organizationBackground,
          content: orgBackground
        }
      }));
    }
  }, [organization, sections.organizationBackground.content]);

  const generateSection = async (sectionKey) => {
    setSections(prev => ({
      ...prev,
      [sectionKey]: { ...prev[sectionKey], loading: true }
    }));
    setError('');

    try {
      const response = await fetch('/api/smart-tools/application/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          section_type: sectionKey,
          grant_title: grantTitle,
          funder_name: funderName,
          request_amount: requestAmount,
          existing_sections: Object.entries(sections).reduce((acc, [key, section]) => {
            if (section.content) acc[key] = section.content;
            return acc;
          }, {})
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate section');
      }

      if (data.success) {
        setSections(prev => ({
          ...prev,
          [sectionKey]: {
            ...prev[sectionKey],
            content: data.content,
            loading: false
          }
        }));
      } else {
        throw new Error(data.error || 'Failed to generate content');
      }
    } catch (err) {
      setError(`Error generating ${sections[sectionKey].title}: ${err.message}`);
      setSections(prev => ({
        ...prev,
        [sectionKey]: { ...prev[sectionKey], loading: false }
      }));
    }
  };

  const generateAllSections = async () => {
    setLoading(true);
    setError('');
    
    for (const sectionKey of Object.keys(sections)) {
      if (!sections[sectionKey].content) {
        await generateSection(sectionKey);
      }
    }
    
    setLoading(false);
    setSuccessMessage('Application generated successfully!');
    setTimeout(() => setSuccessMessage(''), 5000);
  };

  const handleSectionChange = (sectionKey, value) => {
    setSections(prev => ({
      ...prev,
      [sectionKey]: { ...prev[sectionKey], content: value }
    }));
  };

  const downloadApplication = () => {
    let fullContent = `GRANT APPLICATION\n`;
    fullContent += `${'='.repeat(50)}\n\n`;
    
    if (grantTitle) fullContent += `Grant: ${grantTitle}\n`;
    if (funderName) fullContent += `Funder: ${funderName}\n`;
    if (requestAmount) fullContent += `Request Amount: ${requestAmount}\n`;
    if (grantTitle || funderName || requestAmount) fullContent += `\n${'='.repeat(50)}\n\n`;

    Object.entries(sections).forEach(([key, section]) => {
      if (section.content) {
        fullContent += `${section.title.toUpperCase()}\n`;
        fullContent += `${'-'.repeat(section.title.length)}\n\n`;
        fullContent += `${section.content}\n\n`;
      }
    });

    const element = document.createElement('a');
    const file = new Blob([fullContent], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `grant-application-${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const calculateProgress = () => {
    const filledSections = Object.values(sections).filter(s => s.content).length;
    return Math.round((filledSections / Object.keys(sections).length) * 100);
  };

  if (orgLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-pink-600">Loading organization data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white p-6">
      <div className="max-w-6xl mx-auto">
        <Link to="/smart-tools" className="text-pink-600 hover:text-pink-700 mb-4 inline-block">
          ← Back to Smart Tools
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-lg p-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Grant Application Builder
          </h1>
          <p className="text-gray-600 mb-6">
            Build a complete grant application with AI assistance. Each section can be generated individually or all at once.
          </p>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">Progress</span>
              <span className="text-sm font-medium text-pink-600">{calculateProgress()}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-pink-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${calculateProgress()}%` }}
              />
            </div>
          </div>

          {/* Grant Details (Optional) */}
          <div className="mb-8 p-6 bg-pink-50 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Grant Details (Optional)</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Grant Title
                </label>
                <input
                  type="text"
                  value={grantTitle}
                  onChange={(e) => setGrantTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="e.g., Community Impact Grant"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Funder Name
                </label>
                <input
                  type="text"
                  value={funderName}
                  onChange={(e) => setFunderName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="e.g., XYZ Foundation"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Request Amount
                </label>
                <input
                  type="text"
                  value={requestAmount}
                  onChange={(e) => setRequestAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="e.g., $50,000"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 mb-8">
            <button
              onClick={generateAllSections}
              disabled={loading}
              className="px-6 py-3 bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Generating All Sections...' : 'Generate All Sections'}
            </button>
            <button
              onClick={() => setIsTemplateModalOpen(true)}
              className="px-6 py-3 bg-white text-pink-600 border-2 border-pink-600 rounded-lg hover:bg-pink-50"
            >
              Load Template
            </button>
            <button
              onClick={() => setIsSaveTemplateModalOpen(true)}
              disabled={calculateProgress() === 0}
              className="px-6 py-3 bg-white text-pink-600 border-2 border-pink-600 rounded-lg hover:bg-pink-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save as Template
            </button>
            <button
              onClick={downloadApplication}
              disabled={calculateProgress() === 0}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Download Application
            </button>
          </div>

          {/* Success/Error Messages */}
          {successMessage && (
            <div className="mb-6 p-4 bg-green-100 text-green-700 rounded-lg">
              {successMessage}
            </div>
          )}
          {error && (
            <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {/* Application Sections */}
          <div className="space-y-6">
            {Object.entries(sections).map(([key, section]) => (
              <div key={key} className="border rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {section.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {key === 'executiveSummary' && 'Brief overview of your organization and request'}
                      {key === 'organizationBackground' && 'Your organization\'s history, mission, and capacity'}
                      {key === 'needStatement' && 'The problem or need you\'re addressing'}
                      {key === 'projectDescription' && 'Your proposed solution and approach'}
                      {key === 'goalsObjectives' && 'Specific, measurable outcomes you plan to achieve'}
                      {key === 'evaluationPlan' && 'How you\'ll measure and report on success'}
                      {key === 'budgetNarrative' && 'Detailed explanation of how funds will be used'}
                      {key === 'sustainabilityPlan' && 'How the project will continue after grant funding ends'}
                      {key === 'appendix' && 'Additional supporting documents and materials'}
                    </p>
                  </div>
                  <button
                    onClick={() => generateSection(key)}
                    disabled={section.loading}
                    className="px-4 py-2 bg-pink-600 text-white text-sm rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {section.loading ? 'Generating...' : section.content ? 'Regenerate' : 'Generate'}
                  </button>
                </div>
                <textarea
                  value={section.content}
                  onChange={(e) => handleSectionChange(key, e.target.value)}
                  placeholder={`Enter ${section.title.toLowerCase()} here...`}
                  className="w-full h-40 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  disabled={section.loading}
                />
                {section.content && (
                  <div className="mt-2 text-sm text-green-600">
                    ✓ Section completed
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Template Modals */}
      {isTemplateModalOpen && (
        <TemplateSelectionModal
          isOpen={isTemplateModalOpen}
          onClose={() => setIsTemplateModalOpen(false)}
          onSelectTemplate={(template) => {
            if (template.content && typeof template.content === 'object') {
              setSections(prev => ({
                ...prev,
                ...Object.entries(template.content).reduce((acc, [key, value]) => {
                  if (prev[key]) {
                    acc[key] = { ...prev[key], content: value };
                  }
                  return acc;
                }, {})
              }));
            }
            setIsTemplateModalOpen(false);
          }}
          toolType="application"
        />
      )}

      {isSaveTemplateModalOpen && (
        <SaveTemplateModal
          isOpen={isSaveTemplateModalOpen}
          onClose={() => setIsSaveTemplateModalOpen(false)}
          content={sections}
          toolType="application"
          onSuccess={() => {
            setIsSaveTemplateModalOpen(false);
            setSuccessMessage('Template saved successfully!');
            setTimeout(() => setSuccessMessage(''), 5000);
          }}
        />
      )}
    </div>
  );
};

export default GrantApplicationBuilder;