import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOrganization } from '../hooks/useOrganization';
import { getGrant } from '../utils/api';

const SocialMedia = () => {
  const { organization, loading: orgLoading, error: orgError } = useOrganization();
  const [searchParams] = useSearchParams();
  const grantId = searchParams.get('grantId');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [editableContent, setEditableContent] = useState('');
  const [error, setError] = useState('');
  const [platform, setPlatform] = useState('twitter');
  const [topic, setTopic] = useState('');
  const [grant, setGrant] = useState(null);
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantError, setGrantError] = useState('');

  const platforms = [
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: '🐦',
      color: 'from-blue-400 to-blue-500',
      characterLimit: 280,
      tips: ['Use hashtags', 'Keep it concise', 'Engage with questions']
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: '📘',
      color: 'from-blue-600 to-blue-700',
      characterLimit: 2000,
      tips: ['Tell a story', 'Use emojis', 'Include call-to-action']
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: '📸',
      color: 'from-pink-500 to-purple-600',
      characterLimit: 2200,
      tips: ['Visual storytelling', 'Use relevant hashtags', 'Tag locations']
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: '💼',
      color: 'from-blue-700 to-blue-800',
      characterLimit: 3000,
      tips: ['Professional tone', 'Share insights', 'Connect with industry']
    }
  ];

  const selectedPlatform = platforms.find(p => p.id === platform);

  // Fetch grant details when grantId is present
  useEffect(() => {
    if (grantId) {
      const fetchGrantDetails = async () => {
        try {
          setGrantLoading(true);
          setGrantError('');
          const grantData = await getGrant(grantId);
          setGrant(grantData.grant);
          
          // Pre-fill topic with grant-specific content
          if (grantData.grant.title && grantData.grant.funder) {
            setTopic(`Celebrating our grant award: ${grantData.grant.title} from ${grantData.grant.funder}`);
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

  const generateSocialPost = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/smart-tools/social/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform: platform,
          topic: topic || 'General organizational update',
          grant_id: grantId || null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate social media post');
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
    const file = new Blob([editableContent], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${platform}_post.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editableContent);
    alert('Content copied to clipboard!');
  };

  const getCharacterCount = () => {
    return editableContent.length;
  };

  const isOverLimit = () => {
    return getCharacterCount() > selectedPlatform.characterLimit;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/smart-tools" className="text-cyan-600 hover:text-cyan-700 mb-4 inline-block">
            ← Back to Smart Tools
          </Link>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="text-3xl mr-3">📱</span>
              Social Media Generator
            </h1>
            <p className="text-xl text-gray-600">
              Create platform-optimized social media content for your organization
            </p>
            
            {/* Grant Context Banner */}
            {grant && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <span className="font-medium">Grant Context:</span> {grant.title}
                </p>
                <div className="text-sm text-blue-600 mt-1">
                  <span>Funder: {grant.funder}</span>
                  <span className="ml-4">Creating social posts to celebrate this grant</span>
                </div>
              </div>
            )}
            
            {grantError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-700">{grantError}</p>
              </div>
            )}
            
            {organization && (
              <div className="mt-4 p-3 bg-cyan-50 border border-cyan-200 rounded-md">
                <p className="text-cyan-800">
                  <span className="font-medium">Creating content for:</span> {organization.name || 'Your Organization'}
                  {organization.mission && (
                    <span className="text-sm ml-2 text-cyan-600">- {organization.mission}</span>
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
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Post Details</h2>
            
            <div className="space-y-6">
              {/* Platform Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Choose Platform
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {platforms.map((p) => (
                    <motion.button
                      key={p.id}
                      onClick={() => setPlatform(p.id)}
                      className={`relative p-4 rounded-lg border-2 transition-all duration-200 ${
                        platform === p.id
                          ? 'border-cyan-500 bg-cyan-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{p.icon}</span>
                        <div className="text-left">
                          <div className="font-medium text-gray-900">{p.name}</div>
                          <div className="text-xs text-gray-500">
                            {p.characterLimit} chars max
                          </div>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Platform Tips */}
              <div className="bg-gradient-to-r from-cyan-50 to-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-cyan-900 mb-2">
                  {selectedPlatform.icon} {selectedPlatform.name} Tips:
                </h4>
                <ul className="text-sm text-cyan-800 space-y-1">
                  {selectedPlatform.tips.map((tip, index) => (
                    <li key={index}>• {tip}</li>
                  ))}
                </ul>
              </div>

              {/* Topic Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Topic or Theme
                </label>
                <textarea
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., New program launch, fundraising campaign, volunteer appreciation, impact story..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500"
                  rows="3"
                />
              </div>

              <button
                onClick={generateSocialPost}
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-3 px-4 rounded-md hover:from-cyan-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {loading ? 'Generating...' : 'Generate Social Media Post'}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-gradient-to-r from-cyan-50 to-blue-50 border border-cyan-200 rounded-md">
              <h3 className="font-semibold text-cyan-900 mb-2">What you'll get:</h3>
              <ul className="text-sm text-cyan-800 space-y-1">
                <li>• Platform-optimized content</li>
                <li>• Appropriate tone and style</li>
                <li>• Hashtag suggestions</li>
                <li>• Call-to-action included</li>
                <li>• Character count optimization</li>
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
              <h2 className="text-2xl font-semibold text-gray-900">Generated Post</h2>
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
                    className="px-3 py-1 text-sm bg-cyan-100 text-cyan-700 rounded-md hover:bg-cyan-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              )}
            </div>

            {editableContent ? (
              <div className="space-y-4">
                {/* Platform Preview Header */}
                <div className={`bg-gradient-to-r ${selectedPlatform.color} p-3 rounded-lg text-white`}>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{selectedPlatform.icon}</span>
                    <span className="font-medium">{selectedPlatform.name} Post</span>
                  </div>
                </div>

                {/* Character Count */}
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Character count:</span>
                  <span className={`font-medium ${
                    isOverLimit() ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {getCharacterCount()} / {selectedPlatform.characterLimit}
                  </span>
                </div>

                {/* Editable Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Edit your post:
                  </label>
                  <textarea
                    value={editableContent}
                    onChange={(e) => setEditableContent(e.target.value)}
                    className={`w-full p-4 border rounded-md focus:ring-cyan-500 focus:border-cyan-500 ${
                      isOverLimit() ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    rows="8"
                    placeholder="Your generated content will appear here..."
                  />
                  {isOverLimit() && (
                    <p className="mt-2 text-sm text-red-600">
                      ⚠️ Content exceeds {selectedPlatform.name} character limit
                    </p>
                  )}
                </div>

                {/* Platform Preview */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Platform Preview:</h4>
                  <div className="bg-white p-4 rounded border">
                    <div className="flex items-start space-x-3">
                      <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${selectedPlatform.color} flex items-center justify-center text-white text-sm`}>
                        {selectedPlatform.icon}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 text-sm mb-1">Your Organization</div>
                        <div className="text-gray-800 whitespace-pre-wrap">{editableContent}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📱</div>
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  Ready to Create Social Content
                </h3>
                <p className="text-gray-600">
                  Select a platform and topic to generate your optimized social media post
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default SocialMedia;