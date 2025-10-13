import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import GrantNotFound from '../components/GrantNotFound';

const GrantDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [grant, setGrant] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [toolUsage, setToolUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingTools, setLoadingTools] = useState(false);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    fetchGrantDetails();
    fetchToolUsage();
  }, [id]);

  const fetchGrantDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      setNotFound(false);
      
      // Validate grant ID is a number
      if (isNaN(id) || id <= 0) {
        setNotFound(true);
        setLoading(false);
        return;
      }

      const response = await axios.get(`/api/grants/${id}`);
      
      if (response.data.success) {
        setGrant(response.data.grant);
        // Automatically fetch analysis
        fetchAnalysis();
      } else {
        setNotFound(true);
      }
    } catch (err) {
      console.error('Error fetching grant:', err);
      
      // Handle 404 specifically
      if (err.response?.status === 404) {
        setNotFound(true);
      } else {
        setError(err.response?.data?.message || 'Failed to load grant details');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async () => {
    try {
      setAnalyzing(true);
      const response = await axios.get(`/api/grants/${id}/analyze`);
      setAnalysis(response.data.analysis);
    } catch (err) {
      console.error('Error fetching analysis:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const fetchToolUsage = async () => {
    try {
      setLoadingTools(true);
      const response = await axios.get(`/api/workflow/grants/${id}/tool-usage`);
      setToolUsage(response.data);
    } catch (err) {
      console.error('Error fetching tool usage:', err);
      // Don't set error state for tool usage, just log it
    } finally {
      setLoadingTools(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'generated': 'bg-blue-100 text-blue-800',
      'applied': 'bg-green-100 text-green-800',
      'submitted': 'bg-purple-100 text-purple-800',
      'awarded': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRecommendationColor = (recommendation) => {
    const colors = {
      'Highly Recommended': 'bg-green-100 text-green-800 border-green-200',
      'Worth Considering': 'bg-blue-100 text-blue-800 border-blue-200',
      'Consider Carefully': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Not Recommended': 'bg-red-100 text-red-800 border-red-200',
      'Review Manually': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[recommendation] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getAlignmentColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-blue-600';
    if (score >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Show not found component
  if (notFound) {
    return <GrantNotFound />;
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="bg-white shadow rounded-lg p-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading grant details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-white shadow rounded-lg p-8">
          <div className="text-center">
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-red-600 mb-4">{error}</p>
            <Link to="/grants" className="text-pink-600 hover:text-pink-700 font-semibold">
              ← Back to Grants
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!grant) {
    return <GrantNotFound />;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Link to="/grants" className="text-pink-600 hover:text-pink-700 text-sm mb-4 inline-block">
          ← Back to Grant Opportunities
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{grant.title}</h1>
        <p className="text-lg text-gray-600 mt-2">{grant.funder}</p>
      </div>

      {/* Grant Details Card */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Grant Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Amount Range</p>
            <p className="font-medium text-gray-900">
              {grant.amount_min || grant.amount_max ? 
                `$${(grant.amount_min || 0).toLocaleString()} - $${(grant.amount_max || 0).toLocaleString()}` :
                'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Deadline</p>
            <p className="font-medium text-gray-900">
              {grant.deadline ? new Date(grant.deadline).toLocaleDateString() : 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Source</p>
            <p className="font-medium text-gray-900">{grant.source || 'Not specified'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium text-gray-900 capitalize">{grant.status || 'Available'}</p>
          </div>
        </div>
        
        {grant.description && (
          <div className="mt-4">
            <p className="text-sm text-gray-500">Description</p>
            <p className="text-gray-900 mt-1">{grant.description}</p>
          </div>
        )}

        <div className="mt-6 flex gap-3">
          {grant.link && (
            <a 
              href={grant.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
            >
              View Official Grant Page →
            </a>
          )}
          <button
            onClick={() => navigate(`/smart-tools/grant-pitch?grantId=${id}`)}
            className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors"
          >
            Create Grant Pitch
          </button>
        </div>
      </div>

      {/* Tools Used Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Smart Tools Used</h2>
        {loadingTools ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500 mx-auto mb-2"></div>
            <p className="text-gray-600">Loading tool usage...</p>
          </div>
        ) : toolUsage && toolUsage.tools_used && toolUsage.tools_used.length > 0 ? (
          <div>
            <div className="mb-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-500">Total Tools Used</p>
                  <p className="text-2xl font-bold text-gray-900">{toolUsage.summary.total_tools}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-500">Most Used Tool</p>
                  <p className="text-lg font-medium text-gray-900">
                    {Object.keys(toolUsage.summary.by_type).length > 0 ? 
                      Object.entries(toolUsage.summary.by_type).reduce((a, b) => 
                        toolUsage.summary.by_type[a[0]] > toolUsage.summary.by_type[b[0]] ? a : b
                      )[0].replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'None'
                    }
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-500">Applied to Application</p>
                  <p className="text-2xl font-bold text-green-600">
                    {toolUsage.summary.by_status.applied || 0}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              {toolUsage.tools_used.map((tool, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{tool.tool_display_name}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(tool.status)}`}>
                          {tool.status.charAt(0).toUpperCase() + tool.status.slice(1)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        Generated by <span className="font-medium">{tool.user_name}</span> on {formatDate(tool.created_at)}
                      </p>
                      {tool.output_ref && (
                        <p className="text-sm text-gray-700 bg-gray-100 rounded p-2 mt-2">
                          {tool.output_ref.length > 200 ? `${tool.output_ref.substring(0, 200)}...` : tool.output_ref}
                        </p>
                      )}
                    </div>
                    <div className="ml-4">
                      <button 
                        onClick={() => navigate(`/smart-tools?tool=${tool.tool}&grant_id=${id}`)}
                        className="text-pink-600 hover:text-pink-700 text-sm font-medium"
                      >
                        Regenerate
                      </button>
                    </div>
                  </div>
                  {tool.params_json && Object.keys(tool.params_json).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-500 mb-1">Parameters used:</p>
                      <div className="text-xs text-gray-600">
                        {Object.entries(tool.params_json).map(([key, value]) => (
                          <span key={key} className="inline-block mr-3">
                            <span className="font-medium">{key}:</span> {JSON.stringify(value)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Link 
                to={`/smart-tools?grant_id=${id}`}
                className="inline-flex items-center px-4 py-2 border border-pink-300 rounded-md shadow-sm text-sm font-medium text-pink-700 bg-white hover:bg-pink-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500"
              >
                Generate New Content
              </Link>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Smart Tools Used Yet</h3>
            <p className="text-gray-600 mb-4">
              Generate compelling content for this grant using our AI-powered Smart Tools.
            </p>
            <Link 
              to={`/smart-tools?grant_id=${id}`}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-pink-600 hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500"
            >
              Get Started with Smart Tools
            </Link>
          </div>
        )}
      </div>

      {/* AI Analysis Section */}
      {analyzing ? (
        <div className="bg-white shadow rounded-lg p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500 mx-auto mb-3"></div>
            <p className="text-gray-600">Analyzing grant fit and requirements...</p>
          </div>
        </div>
      ) : analysis ? (
        <div className="space-y-6">
          {/* Decision Recommendation */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Recommendation</h2>
            <div className={`inline-flex px-4 py-2 rounded-full font-medium border ${getRecommendationColor(analysis.decision_recommendation)}`}>
              {analysis.decision_recommendation}
            </div>
            <p className="text-gray-700 mt-3">{analysis.decision_rationale}</p>
            
            {/* Alignment Score */}
            <div className="mt-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Alignment Score:</span>
                <span className={`text-2xl font-bold ${getAlignmentColor(analysis.alignment_score)}`}>
                  {analysis.alignment_score}/10
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">{analysis.alignment_explanation}</p>
            </div>
          </div>

          {/* Key Requirements */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Requirements</h3>
            <ul className="space-y-2">
              {(analysis.key_requirements || []).map((req, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-pink-500 mr-2">•</span>
                  <span className="text-gray-700">{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Success Factors */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Success Factors</h3>
            <ul className="space-y-2">
              {(analysis.success_factors || []).map((factor, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">{factor}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Potential Challenges */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Potential Challenges</h3>
            <ul className="space-y-2">
              {(analysis.potential_challenges || []).map((challenge, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-yellow-500 mr-2">⚠</span>
                  <span className="text-gray-700">{challenge}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Recommended Approach */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Recommended Approach</h3>
            <ol className="space-y-2">
              {(analysis.recommended_approach || []).map((step, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-pink-500 font-medium mr-2">{index + 1}.</span>
                  <span className="text-gray-700">{step}</span>
                </li>
              ))}
            </ol>
            <p className="text-sm text-gray-600 mt-4">
              <span className="font-medium">Time Estimate:</span> {analysis.time_estimate || 'Not specified'}
            </p>
          </div>

          {/* Next Steps */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Next Steps</h3>
            <ul className="space-y-2">
              {(analysis.next_steps || []).map((step, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span className="text-gray-700">{step}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Preparation Checklist */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Preparation Checklist</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {(analysis.preparation_checklist || []).map((item, index) => (
                <label key={index} className="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" className="rounded text-pink-500 focus:ring-pink-500" />
                  <span className="text-gray-700">{item}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Similar Opportunities */}
          {analysis.similar_opportunities && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Finding Similar Opportunities</h3>
              <ul className="space-y-1">
                {(analysis.similar_opportunities || []).map((opp, index) => (
                  <li key={index} className="text-gray-700">• {opp}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-600 text-center">
            AI analysis not available. Please review the grant details manually.
          </p>
        </div>
      )}
    </div>
  );
};

export default GrantDetail;