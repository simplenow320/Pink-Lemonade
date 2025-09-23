import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOrganization } from '../../hooks/useOrganization';

const TemplateSelectionModal = ({ 
  isOpen, 
  onClose, 
  toolType,
  onTemplateSelect 
}) => {
  const { organization } = useOrganization();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    tags: [],
    focus_areas: [],
    funder_types: []
  });
  
  // Available filter options
  const availableTags = ['education', 'health', 'environment', 'arts', 'community', 'research'];
  const availableFocusAreas = ['education', 'health', 'environment', 'social-services', 'arts-culture', 'research'];
  const availableFunderTypes = ['foundation', 'government', 'corporate', 'individual'];

  // Fetch templates when modal opens
  useEffect(() => {
    if (isOpen && organization?.id) {
      fetchTemplates();
    }
  }, [isOpen, organization?.id, toolType, filters]);

  const fetchTemplates = async () => {
    if (!organization?.id) return;
    
    setLoading(true);
    setError('');
    
    try {
      const params = new URLSearchParams({
        organization_id: organization.id.toString(),
        ...(toolType && { tool_type: toolType }),
        ...Object.entries(filters).reduce((acc, [key, values]) => {
          values.forEach(value => acc.append(key, value));
          return acc;
        }, new URLSearchParams())
      });

      const response = await fetch(`/api/templates/smart-tools?${params}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch templates');
      }

      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = async (template) => {
    try {
      // Mark template as used
      await fetch(`/api/templates/smart-tools/${template.id}/use`, {
        method: 'POST'
      });

      // Get template parameters
      const response = await fetch(`/api/templates/smart-tools/${template.id}/parameters`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to load template');
      }

      // Pass the template parameters to parent component
      onTemplateSelect({
        id: template.id,
        name: template.name,
        parameters: data.parameters,
        generated_content: data.generated_content
      });

      onClose();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleFilter = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType].includes(value)
        ? prev[filterType].filter(item => item !== value)
        : [...prev[filterType], value]
    }));
  };

  const clearFilters = () => {
    setFilters({
      tags: [],
      focus_areas: [],
      funder_types: []
    });
  };

  const handleClose = () => {
    setSelectedTemplate(null);
    setPreviewVisible(false);
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
          className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex justify-between items-center p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Select Template
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {toolType ? `Templates for ${toolType.replace('_', ' ')}` : 'All Smart Tools templates'}
              </p>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Filters Sidebar */}
            <div className="w-64 border-r border-gray-200 p-4 overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-medium text-gray-900">Filters</h3>
                <button
                  onClick={clearFilters}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Clear all
                </button>
              </div>

              {/* Tags Filter */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Tags</h4>
                <div className="space-y-2">
                  {availableTags.map(tag => (
                    <label key={tag} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.tags.includes(tag)}
                        onChange={() => toggleFilter('tags', tag)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600 capitalize">{tag}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Focus Areas Filter */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Focus Areas</h4>
                <div className="space-y-2">
                  {availableFocusAreas.map(area => (
                    <label key={area} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.focus_areas.includes(area)}
                        onChange={() => toggleFilter('focus_areas', area)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600 capitalize">{area.replace('-', ' ')}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Funder Types Filter */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Funder Types</h4>
                <div className="space-y-2">
                  {availableFunderTypes.map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.funder_types.includes(type)}
                        onChange={() => toggleFilter('funder_types', type)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600 capitalize">{type}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex overflow-hidden">
              {/* Templates List */}
              <div className="flex-1 p-6 overflow-y-auto">
                {error && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                )}

                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-gray-600">Loading templates...</span>
                  </div>
                ) : templates.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
                    <p className="mt-1 text-sm text-gray-500">Try adjusting your filters or create your first template.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                          selectedTemplate?.id === template.id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedTemplate(template)}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium text-gray-900">{template.name}</h4>
                          <div className="flex space-x-2">
                            {template.is_shared && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Shared
                              </span>
                            )}
                            {!template.created_by_same_org && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                Community
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {template.description && (
                          <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                        )}
                        
                        {template.preview && (
                          <p className="text-xs text-gray-500 mb-3 italic">
                            "{template.preview}"
                          </p>
                        )}

                        <div className="flex flex-wrap gap-1 mb-2">
                          {template.tags?.map(tag => (
                            <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              {tag}
                            </span>
                          ))}
                        </div>

                        <div className="flex justify-between items-center text-xs text-gray-500">
                          <span>Used {template.times_used} times</span>
                          <span>{new Date(template.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Template Preview */}
              {selectedTemplate && (
                <div className="w-80 border-l border-gray-200 p-6 overflow-y-auto bg-gray-50">
                  <h3 className="font-medium text-gray-900 mb-4">Template Preview</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-1">{selectedTemplate.name}</h4>
                      {selectedTemplate.description && (
                        <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
                      )}
                    </div>

                    {selectedTemplate.tags && selectedTemplate.tags.length > 0 && (
                      <div>
                        <h5 className="text-xs font-medium text-gray-700 mb-2">Tags</h5>
                        <div className="flex flex-wrap gap-1">
                          {selectedTemplate.tags.map(tag => (
                            <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h5 className="text-xs font-medium text-gray-700 mb-2">Usage Stats</h5>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div>Used: {selectedTemplate.times_used} times</div>
                        <div>Success Rate: {(selectedTemplate.success_rate * 100).toFixed(1)}%</div>
                        <div>Rating: {selectedTemplate.avg_rating}/5.0</div>
                      </div>
                    </div>

                    {selectedTemplate.preview && (
                      <div>
                        <h5 className="text-xs font-medium text-gray-700 mb-2">Content Preview</h5>
                        <div className="text-xs text-gray-600 bg-white p-3 rounded border max-h-32 overflow-y-auto">
                          {selectedTemplate.preview}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
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
              onClick={() => selectedTemplate && handleTemplateSelect(selectedTemplate)}
              disabled={!selectedTemplate}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Use Template
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default TemplateSelectionModal;