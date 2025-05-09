import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getGrant, 
  getWritingAssistantSections, 
  generateWritingSection, 
  improveWritingSection, 
  generateSectionOutline 
} from '../utils/api';
import { useNotification } from '../context/NotificationContext';

const WritingAssistantPage = () => {
  const { grantId } = useParams();
  const navigate = useNavigate();
  const { addSuccess, addError } = useNotification();
  
  const [loading, setLoading] = useState(false);
  const [sectionTypes, setSectionTypes] = useState({});
  const [selectedSection, setSelectedSection] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [feedback, setFeedback] = useState('');
  const [writingTips, setWritingTips] = useState([]);
  const [grantInfo, setGrantInfo] = useState(null);
  const [mode, setMode] = useState('generate'); // generate, edit, improve, outline
  const [outline, setOutline] = useState('');
  const [additionalInputs, setAdditionalInputs] = useState('');

  // Fetch section types on mount
  useEffect(() => {
    const fetchSectionTypes = async () => {
      try {
        const data = await getWritingAssistantSections();
        if (data.success) {
          setSectionTypes(data.sections);
        } else {
          addError('Failed to fetch section types');
        }
      } catch (error) {
        console.error('Error fetching section types:', error);
        addError('Failed to fetch section types: ' + error.message);
      }
    };

    fetchSectionTypes();
  }, [addError]);

  // Fetch grant info if grantId is provided
  useEffect(() => {
    if (grantId) {
      const fetchGrantInfo = async () => {
        try {
          const data = await getGrant(grantId);
          setGrantInfo(data);
        } catch (error) {
          console.error('Error fetching grant:', error);
          addError('Failed to fetch grant: ' + error.message);
        }
      };

      fetchGrantInfo();
    }
  }, [grantId, addError]);

  const handleSectionChange = (e) => {
    setSelectedSection(e.target.value);
    // Reset content when changing sections
    setGeneratedContent('');
    setOriginalContent('');
    setFeedback('');
    setOutline('');
  };

  const handleGenerateContent = async () => {
    if (!selectedSection) {
      addError('Please select a section type');
      return;
    }

    if (!grantId) {
      addError('No grant selected. Please select a grant first.');
      return;
    }

    setLoading(true);
    try {
      // Parse additional inputs as JSON if provided
      let parsedInputs = {};
      if (additionalInputs.trim()) {
        try {
          // Split by newlines and convert to key-value pairs
          const inputLines = additionalInputs.split('\n').filter(line => line.trim());
          inputLines.forEach(line => {
            const [key, ...valueParts] = line.split(':');
            if (key && valueParts.length) {
              parsedInputs[key.trim()] = valueParts.join(':').trim();
            }
          });
        } catch (e) {
          addError('Could not parse additional inputs. Please use format "Key: Value" with each entry on a new line.');
          setLoading(false);
          return;
        }
      }

      const response = await axios.post('/api/writing-assistant/generate', {
        section_type: selectedSection,
        grant_id: grantId,
        additional_inputs: Object.keys(parsedInputs).length ? parsedInputs : undefined
      });

      if (response.data.success) {
        setGeneratedContent(response.data.content);
        setOriginalContent(response.data.content);
        setWritingTips(response.data.writing_tips || []);
        setMode('edit');
        addSuccess('Content generated successfully');
      } else {
        addError(response.data.error || 'Failed to generate content');
      }
    } catch (error) {
      console.error('Error generating content:', error);
      addError('Failed to generate content: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateOutline = async () => {
    if (!selectedSection) {
      addError('Please select a section type');
      return;
    }

    if (!grantId) {
      addError('No grant selected. Please select a grant first.');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/writing-assistant/outline', {
        section_type: selectedSection,
        grant_id: grantId
      });

      if (response.data.success) {
        setOutline(response.data.outline);
        setMode('outline');
        addSuccess('Outline generated successfully');
      } else {
        addError(response.data.error || 'Failed to generate outline');
      }
    } catch (error) {
      console.error('Error generating outline:', error);
      addError('Failed to generate outline: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleImproveContent = async () => {
    if (!selectedSection || !generatedContent || !feedback) {
      addError('Please provide section type, content, and feedback');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/writing-assistant/improve', {
        section_type: selectedSection,
        content: generatedContent,
        feedback: feedback
      });

      if (response.data.success) {
        setGeneratedContent(response.data.content);
        setFeedback('');
        addSuccess('Content improved successfully');
      } else {
        addError(response.data.error || 'Failed to improve content');
      }
    } catch (error) {
      console.error('Error improving content:', error);
      addError('Failed to improve content: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (mode === 'edit' || mode === 'improve') {
      // Reset to original content
      setGeneratedContent(originalContent);
      setFeedback('');
    } else if (mode === 'outline') {
      // Clear outline
      setOutline('');
      setMode('generate');
    }
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    
    // Reset certain fields based on mode change
    if (newMode === 'generate') {
      setGeneratedContent('');
      setOriginalContent('');
      setFeedback('');
      setOutline('');
    }
  };

  // Render different UI based on mode
  const renderContent = () => {
    if (mode === 'generate') {
      return (
        <div className="mt-4">
          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium">Additional Context (Optional)</label>
            <p className="text-xs text-gray-500 mb-2">
              Add key-value pairs, one per line (e.g., "Project Timeline: 12 months")
            </p>
            <textarea 
              className="w-full p-2 border rounded-md"
              rows="4"
              placeholder="Key: Value (one per line)"
              value={additionalInputs}
              onChange={(e) => setAdditionalInputs(e.target.value)}
            />
          </div>
          
          <div className="flex space-x-2">
            <button
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
              onClick={handleGenerateContent}
              disabled={loading || !selectedSection || !grantId}
            >
              {loading ? 'Generating...' : 'Generate Content'}
            </button>
            
            <button
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50"
              onClick={handleGenerateOutline}
              disabled={loading || !selectedSection || !grantId}
            >
              {loading ? 'Generating...' : 'Generate Outline'}
            </button>
          </div>
        </div>
      );
    } else if (mode === 'outline') {
      return (
        <div className="mt-4">
          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium">Section Outline</label>
            <div className="prose max-w-none p-4 bg-gray-50 rounded-md border whitespace-pre-wrap">
              {outline}
            </div>
          </div>
          
          <div className="flex space-x-2 mt-4">
            <button
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              onClick={() => handleModeChange('generate')}
            >
              Generate New Content
            </button>
            
            <button
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              onClick={handleGenerateContent}
              disabled={loading}
            >
              Use Outline to Generate Content
            </button>
          </div>
        </div>
      );
    } else if (mode === 'edit' || mode === 'improve') {
      return (
        <div className="mt-4">
          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium">Generated Content</label>
            <textarea 
              className="w-full p-2 border rounded-md font-mono text-sm"
              rows="12"
              value={generatedContent}
              onChange={(e) => setGeneratedContent(e.target.value)}
            />
          </div>
          
          {writingTips.length > 0 && (
            <div className="mb-4 p-3 bg-blue-50 rounded-md">
              <h4 className="font-medium text-blue-800 mb-2">Writing Tips</h4>
              <ul className="list-disc pl-5 text-sm text-blue-700 space-y-1">
                {writingTips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium">Feedback for Improvement</label>
            <textarea 
              className="w-full p-2 border rounded-md"
              rows="3"
              placeholder="Describe how you want to improve this content..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
          
          <div className="flex space-x-2">
            <button
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
              onClick={handleImproveContent}
              disabled={loading || !feedback}
            >
              {loading ? 'Improving...' : 'Improve Content'}
            </button>
            
            <button
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
              onClick={handleReset}
              disabled={loading}
            >
              Reset Changes
            </button>
            
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              onClick={() => handleModeChange('generate')}
              disabled={loading}
            >
              Start New
            </button>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Writing Assistant</h1>
        {!grantId && (
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => navigate('/grants')}
          >
            Select a Grant
          </button>
        )}
      </div>
      
      {grantInfo && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow">
          <h2 className="text-lg font-medium text-gray-800 mb-2">Working with: {grantInfo.title}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Funder:</span> {grantInfo.funder}
            </div>
            <div>
              <span className="font-medium">Amount:</span> ${grantInfo.amount?.toLocaleString() || 'N/A'}
            </div>
            <div>
              <span className="font-medium">Focus Areas:</span> {grantInfo.focus_areas?.join(', ') || 'N/A'}
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-6">
          <label className="block mb-2 text-sm font-medium">Select Section Type</label>
          <select 
            className="w-full p-2 border rounded-md"
            value={selectedSection}
            onChange={handleSectionChange}
          >
            <option value="">-- Select a section --</option>
            {Object.entries(sectionTypes).map(([key, description]) => (
              <option key={key} value={key}>{description}</option>
            ))}
          </select>
        </div>
        
        {renderContent()}
      </div>
    </div>
  );
};

export default WritingAssistantPage;