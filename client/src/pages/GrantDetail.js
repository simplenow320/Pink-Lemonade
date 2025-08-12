import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const GrantDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [grant, setGrant] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGrantDetails();
  }, [id]);

  const fetchGrantDetails = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/grants/${id}`);
      setGrant(response.data.grant);
      
      // Automatically fetch analysis
      fetchAnalysis();
    } catch (err) {
      setError('Failed to load grant details');
      console.error('Error fetching grant:', err);
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

  if (error || !grant) {
    return (
      <div className="p-6">
        <div className="bg-white shadow rounded-lg p-8">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || 'Grant not found'}</p>
            <Link to="/grants" className="text-pink-600 hover:text-pink-700">
              ← Back to Grants
            </Link>
          </div>
        </div>
      </div>
    );
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