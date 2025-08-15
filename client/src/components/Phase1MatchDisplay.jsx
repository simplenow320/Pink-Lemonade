import React, { useState, useEffect } from 'react';
import { ChevronRight, Heart, Star, MapPin, Calendar, DollarSign, Target, Award } from 'lucide-react';

/**
 * Phase 1: Clean Match Display Component
 * Maintains Pink Lemonade branding (pink, white, black, grey)
 */
const Phase1MatchDisplay = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState('all');
  const [stats, setStats] = useState(null);

  // Pink Lemonade color palette
  const colors = {
    pink: '#EC4899',
    lightPink: '#FBCFE8',
    white: '#FFFFFF',
    black: '#000000',
    grey: '#6B7280',
    lightGrey: '#F3F4F6'
  };

  useEffect(() => {
    fetchMatches();
    fetchStats();
  }, []);

  const fetchMatches = async (source = 'all') => {
    setLoading(true);
    try {
      const endpoint = source === 'all' 
        ? '/api/phase1/match/all'
        : `/api/phase1/match/${source}`;
      
      const response = await fetch(endpoint);
      const data = await response.json();
      
      if (data.success) {
        setMatches(data.matches || data.opportunities || []);
      }
    } catch (error) {
      console.error('Error fetching matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/phase1/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleLoveGrant = async (match) => {
    try {
      const response = await fetch('/api/phase1/match/0/love', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opportunity_data: match })
      });
      
      const data = await response.json();
      if (data.success) {
        // Update UI to show grant was loved
        const updatedMatches = matches.map(m => 
          m === match ? { ...m, loved: true } : m
        );
        setMatches(updatedMatches);
      }
    } catch (error) {
      console.error('Error loving grant:', error);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return colors.pink;
    if (score >= 60) return '#10B981'; // Green
    if (score >= 40) return '#F59E0B'; // Orange
    return colors.grey;
  };

  const MatchCard = ({ match }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
      {/* Match Score Badge */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
          <div 
            className="text-2xl font-bold"
            style={{ color: getScoreColor(match.match_score) }}
          >
            {match.match_score}%
          </div>
          <div className="text-sm text-gray-500">Match</div>
        </div>
        <button
          onClick={() => handleLoveGrant(match)}
          className={`p-2 rounded-full transition-colors ${
            match.loved 
              ? 'bg-pink-100 text-pink-500' 
              : 'hover:bg-gray-100 text-gray-400'
          }`}
        >
          <Heart 
            size={20} 
            fill={match.loved ? colors.pink : 'none'}
          />
        </button>
      </div>

      {/* Grant Title */}
      <h3 className="text-lg font-semibold text-black mb-2 line-clamp-2">
        {match.title}
      </h3>

      {/* Funder */}
      <div className="flex items-center gap-2 text-gray-600 mb-3">
        <Award size={16} />
        <span className="text-sm">{match.funder}</span>
      </div>

      {/* Key Details */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {match.amount_range && match.amount_range !== 'Varies' && (
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <DollarSign size={14} />
            <span>{match.amount_range}</span>
          </div>
        )}
        {match.deadline && match.deadline !== 'See article' && (
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <Calendar size={14} />
            <span>
              {new Date(match.deadline).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {/* Match Reasoning */}
      <div className="bg-gray-50 rounded p-3 mb-4">
        <p className="text-sm text-gray-600">
          {match.match_reasoning}
        </p>
      </div>

      {/* Source Badge */}
      <div className="flex justify-between items-center">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          match.source === 'Federal Register' ? 'bg-blue-100 text-blue-700' :
          match.source === 'Candid' ? 'bg-purple-100 text-purple-700' :
          match.source === 'Foundation Directory' ? 'bg-green-100 text-green-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {match.source}
        </span>
        
        {match.url && (
          <a
            href={match.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-pink-500 hover:text-pink-600 flex items-center gap-1 text-sm font-medium"
          >
            View Details
            <ChevronRight size={16} />
          </a>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-black mb-2">
          Grant Matches
        </h1>
        <p className="text-gray-600">
          AI-powered matches from 5 verified data sources
        </p>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="text-2xl font-bold" style={{ color: colors.pink }}>
                {stats.total_opportunities}
              </div>
              <div className="text-sm text-gray-600">Total Opportunities</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-black">
                {stats.profile_completeness}%
              </div>
              <div className="text-sm text-gray-600">Profile Complete</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-black">
                {Object.values(stats.sources || {}).filter(v => v > 0).length}
              </div>
              <div className="text-sm text-gray-600">Active Sources</div>
            </div>
            <div>
              <div className="text-lg font-bold" style={{ color: colors.pink }}>
                {stats.matching_quality}
              </div>
              <div className="text-sm text-gray-600">Match Quality</div>
            </div>
          </div>
        </div>
      )}

      {/* Source Filter */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => {
            setSelectedSource('all');
            fetchMatches('all');
          }}
          className={`px-4 py-2 rounded-full font-medium transition-colors ${
            selectedSource === 'all'
              ? 'bg-pink-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All Sources
        </button>
        <button
          onClick={() => {
            setSelectedSource('federal');
            fetchMatches('federal');
          }}
          className={`px-4 py-2 rounded-full font-medium transition-colors ${
            selectedSource === 'federal'
              ? 'bg-pink-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Federal
        </button>
        <button
          onClick={() => {
            setSelectedSource('foundations');
            fetchMatches('foundations');
          }}
          className={`px-4 py-2 rounded-full font-medium transition-colors ${
            selectedSource === 'foundations'
              ? 'bg-pink-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Foundations
        </button>
        <button
          onClick={() => {
            setSelectedSource('candid-grants');
            fetchMatches('candid-grants');
          }}
          className={`px-4 py-2 rounded-full font-medium transition-colors ${
            selectedSource === 'candid-grants'
              ? 'bg-pink-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Candid
        </button>
      </div>

      {/* Matches Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2" 
               style={{ borderColor: colors.pink }}></div>
        </div>
      ) : matches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {matches.map((match, index) => (
            <MatchCard key={index} match={match} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Target size={48} className="mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No matches found
          </h3>
          <p className="text-gray-600">
            Complete your organization profile to improve matching
          </p>
        </div>
      )}
    </div>
  );
};

export default Phase1MatchDisplay;