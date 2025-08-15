import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Templates = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('templates');
  const [templates, setTemplates] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch templates status
      const statusResponse = await fetch('/api/templates/status');
      const statusData = await statusResponse.json();
      
      // Fetch categories
      const categoriesResponse = await fetch('/api/templates/categories');
      const categoriesData = await categoriesResponse.json();
      setCategories(categoriesData.categories || []);
      
      // Set mock templates for demonstration
      setTemplates([
        {
          id: 1,
          name: 'Standard Grant Proposal',
          description: 'Complete grant proposal with all standard sections',
          category: 'Proposals',
          type: 'grant_proposal',
          typical_length: '10-15 pages',
          time_to_complete: '30 minutes',
          difficulty_level: 'moderate',
          times_used: 234,
          success_rate: 31.5,
          avg_rating: 4.7
        },
        {
          id: 2,
          name: 'Letter of Inquiry (LOI)',
          description: 'Concise introduction letter for initial funder contact',
          category: 'Letters',
          type: 'letter_of_inquiry',
          typical_length: '2-3 pages',
          time_to_complete: '15 minutes',
          difficulty_level: 'easy',
          times_used: 189,
          success_rate: 28.3,
          avg_rating: 4.5
        },
        {
          id: 3,
          name: 'Budget Justification',
          description: 'Detailed explanation of project budget and costs',
          category: 'Budgets',
          type: 'budget_justification',
          typical_length: '3-5 pages',
          time_to_complete: '20 minutes',
          difficulty_level: 'moderate',
          times_used: 156,
          success_rate: 35.2,
          avg_rating: 4.8
        },
        {
          id: 4,
          name: 'Impact Statement',
          description: 'Compelling narrative of your program\'s outcomes',
          category: 'Statements',
          type: 'impact_statement',
          typical_length: '2-4 pages',
          time_to_complete: '25 minutes',
          difficulty_level: 'moderate',
          times_used: 142,
          success_rate: 29.7,
          avg_rating: 4.6
        },
        {
          id: 5,
          name: 'Executive Summary',
          description: 'High-level overview of your grant proposal',
          category: 'Summaries',
          type: 'executive_summary',
          typical_length: '1-2 pages',
          time_to_complete: '10 minutes',
          difficulty_level: 'easy',
          times_used: 278,
          success_rate: 33.1,
          avg_rating: 4.9
        }
      ]);
      
      // Set mock documents
      setDocuments([
        {
          id: 1,
          title: 'Education Grant Proposal - March 2025',
          template_name: 'Standard Grant Proposal',
          grant_name: 'Youth Education Initiative',
          status: 'draft',
          completion_percentage: 75,
          word_count: 3248,
          updated_at: '2025-03-14T10:30:00'
        },
        {
          id: 2,
          title: 'Community Health LOI - February 2025',
          template_name: 'Letter of Inquiry',
          grant_name: 'Health Equity Grant',
          status: 'final',
          completion_percentage: 100,
          word_count: 892,
          updated_at: '2025-02-28T14:15:00'
        },
        {
          id: 3,
          title: 'Arts Program Budget - January 2025',
          template_name: 'Budget Justification',
          grant_name: 'Arts & Culture Fund',
          status: 'submitted',
          completion_percentage: 100,
          word_count: 1567,
          updated_at: '2025-01-15T09:45:00'
        }
      ]);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDocument = (template) => {
    setSelectedTemplate(template);
    setShowGenerateModal(true);
  };

  const confirmGenerate = () => {
    // Here would be the actual generation logic
    alert(`Generating ${selectedTemplate.name}...`);
    setShowGenerateModal(false);
    setSelectedTemplate(null);
    // Navigate to document editor
    navigate('/templates/document/new');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'bg-yellow-100 text-yellow-800';
      case 'in_review': return 'bg-blue-100 text-blue-800';
      case 'final': return 'bg-green-100 text-green-800';
      case 'submitted': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyColor = (level) => {
    switch (level) {
      case 'easy': return 'text-green-600';
      case 'moderate': return 'text-yellow-600';
      case 'advanced': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Smart Templates</h1>
                <p className="mt-1 text-sm text-gray-500">
                  Phase 5: AI-powered document generation saving 10-15 hours per grant
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-4 py-2 rounded-lg">
                  <div className="text-xs opacity-90">Time Saved</div>
                  <div className="text-lg font-bold">847 hours</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('templates')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'templates'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📝 Templates
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'documents'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📄 My Documents
            </button>
            <button
              onClick={() => setActiveTab('library')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'library'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📚 Content Library
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'templates' && (
          <div>
            {/* Template Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Templates Available</p>
                    <p className="text-2xl font-bold text-gray-900">12</p>
                  </div>
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Avg. Time Saved</p>
                    <p className="text-2xl font-bold text-green-600">12.5 hrs</p>
                  </div>
                  <div className="bg-green-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Success Rate</p>
                    <p className="text-2xl font-bold text-purple-600">31%</p>
                  </div>
                  <div className="bg-purple-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">AI Enhanced</p>
                    <p className="text-2xl font-bold text-pink-600">100%</p>
                  </div>
                  <div className="bg-pink-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Template Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map(template => (
                <div key={template.id} className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{template.category}</p>
                      </div>
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700">{template.avg_rating}</span>
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-4">{template.description}</p>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm">
                        <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-gray-600">{template.time_to_complete}</span>
                      </div>
                      <div className="flex items-center text-sm">
                        <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-gray-600">{template.typical_length}</span>
                      </div>
                      <div className="flex items-center text-sm">
                        <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        <span className={`font-medium ${getDifficultyColor(template.difficulty_level)}`}>
                          {template.difficulty_level.charAt(0).toUpperCase() + template.difficulty_level.slice(1)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between pt-4 border-t">
                      <div className="text-xs text-gray-500">
                        Used {template.times_used} times • {template.success_rate}% success
                      </div>
                      <button
                        onClick={() => handleGenerateDocument(template)}
                        className="px-4 py-2 bg-pink-500 text-white text-sm font-medium rounded-lg hover:bg-pink-600 transition-colors"
                      >
                        Generate
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'documents' && (
          <div>
            <div className="bg-white rounded-xl shadow-sm">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Documents</h2>
                <div className="space-y-4">
                  {documents.map(doc => (
                    <div key={doc.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{doc.title}</h3>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span>{doc.template_name}</span>
                            <span>•</span>
                            <span>{doc.word_count} words</span>
                            <span>•</span>
                            <span>{new Date(doc.updated_at).toLocaleDateString()}</span>
                          </div>
                          {doc.grant_name && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-500">Grant: </span>
                              <span className="text-sm text-gray-700">{doc.grant_name}</span>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">{doc.completion_percentage}%</div>
                            <div className="w-20 bg-gray-200 rounded-full h-2 mt-1">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${doc.completion_percentage}%` }}
                              />
                            </div>
                          </div>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                            {doc.status}
                          </span>
                          <button className="p-2 text-gray-400 hover:text-gray-600">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'library' && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Content Library</h2>
            <p className="text-gray-600 mb-6">
              Save and reuse successful content across your grant applications
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-gray-900">Mission Statement</h3>
                <p className="text-sm text-gray-600 mt-2">
                  Your organization's mission statement, ready to use in any application
                </p>
                <div className="mt-3 flex items-center text-xs text-gray-500">
                  <span>Used 45 times</span>
                  <span className="mx-2">•</span>
                  <span>Last updated 2 days ago</span>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-gray-900">Impact Metrics 2024</h3>
                <p className="text-sm text-gray-600 mt-2">
                  Key performance indicators and success metrics from last year
                </p>
                <div className="mt-3 flex items-center text-xs text-gray-500">
                  <span>Used 23 times</span>
                  <span className="mx-2">•</span>
                  <span>Last updated 1 week ago</span>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-gray-900">Program Description</h3>
                <p className="text-sm text-gray-600 mt-2">
                  Detailed description of your core programs and services
                </p>
                <div className="mt-3 flex items-center text-xs text-gray-500">
                  <span>Used 67 times</span>
                  <span className="mx-2">•</span>
                  <span>Last updated 3 days ago</span>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-gray-900">Board & Leadership</h3>
                <p className="text-sm text-gray-600 mt-2">
                  Information about your board members and leadership team
                </p>
                <div className="mt-3 flex items-center text-xs text-gray-500">
                  <span>Used 34 times</span>
                  <span className="mx-2">•</span>
                  <span>Last updated 1 month ago</span>
                </div>
              </div>
            </div>
            
            <button className="mt-6 px-4 py-2 bg-pink-500 text-white font-medium rounded-lg hover:bg-pink-600 transition-colors">
              + Add New Content
            </button>
          </div>
        )}
      </div>

      {/* Generate Modal */}
      {showGenerateModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Generate {selectedTemplate.name}
            </h3>
            <p className="text-gray-600 mb-6">
              This will create a new document using AI to generate initial content based on your organization's profile.
            </p>
            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <p className="text-sm text-blue-800">
                <strong>Time to complete:</strong> {selectedTemplate.time_to_complete}<br />
                <strong>Typical length:</strong> {selectedTemplate.typical_length}<br />
                <strong>AI-enhanced:</strong> Yes, using GPT-4o
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmGenerate}
                className="flex-1 px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600"
              >
                Generate Document
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="bg-gradient-to-r from-pink-500 to-purple-600 text-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Phase 5 Smart Templates</p>
              <p className="text-lg font-semibold">Saving 85% of grant writing time</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">100% AI-Powered</p>
              <p className="text-sm opacity-90">Using GPT-4o for intelligent generation</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Templates;