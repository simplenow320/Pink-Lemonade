import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const UseInApplicationModal = ({ 
  isOpen, 
  onClose, 
  content, 
  sourceTool, 
  grantId, 
  onSuccess 
}) => {
  const [selectedSection, setSelectedSection] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Application sections available for selection
  const sections = [
    { value: 'need_statement', label: 'Need Statement / Problem Description' },
    { value: 'approach', label: 'Approach / Methodology' },
    { value: 'budget_narrative', label: 'Budget Narrative / Justification' },
    { value: 'cover_letter', label: 'Cover Letter / Executive Summary' },
    { value: 'organization_background', label: 'Organization Background' },
    { value: 'project_description', label: 'Project Description' },
    { value: 'evaluation_plan', label: 'Evaluation Plan' },
    { value: 'sustainability_plan', label: 'Sustainability Plan' },
    { value: 'impact_statement', label: 'Impact Statement' },
    { value: 'appendix', label: 'Appendix / Supporting Materials' }
  ];

  const handleSave = async () => {
    if (!selectedSection) {
      setError('Please select a section');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const response = await fetch(`/api/workflow/applications/${grantId}/content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          section: selectedSection,
          content: content,
          source_tool: sourceTool,
          tool_usage_id: `${sourceTool}_${Date.now()}`
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to save content');
      }

      if (data.success) {
        // Call success callback with deep link info
        onSuccess(data);
        onClose();
      } else {
        throw new Error(data.error || 'Failed to save content');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setSelectedSection('');
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
        >
          {/* Header */}
          <div className="flex justify-between items-center p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Use in Application
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <p className="text-gray-600 mb-4">
              Save this generated content to your grant application. Select the section where this content should be placed.
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Application Section
              </label>
              <select
                value={selectedSection}
                onChange={(e) => setSelectedSection(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select a section...</option>
                {sections.map((section) => (
                  <option key={section.value} value={section.value}>
                    {section.label}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Preview */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content Preview
              </label>
              <div className="max-h-32 overflow-y-auto p-3 bg-gray-50 border border-gray-200 rounded-md">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {content.length > 300 ? `${content.substring(0, 300)}...` : content}
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !selectedSection}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving...' : 'Save to Application'}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default UseInApplicationModal;