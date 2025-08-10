import React, { useState, useEffect } from 'react';

const ProfileRewards = ({ completionPercentage = 0, completedSections = [], totalSections = 5 }) => {
  const [showCelebration, setShowCelebration] = useState(false);
  const [previousCompletion, setPreviousCompletion] = useState(completionPercentage);

  // Badge definitions
  const badges = [
    {
      id: 'started',
      name: 'Getting Started',
      description: 'You began your profile setup',
      icon: '🚀',
      threshold: 10,
      color: 'pink'
    },
    {
      id: 'half-way',
      name: 'Making Progress',
      description: 'You are halfway done with your profile',
      icon: '⭐',
      threshold: 50,
      color: 'pink'
    },
    {
      id: 'almost-there',
      name: 'Almost Ready',
      description: 'Your profile is nearly complete',
      icon: '🎯',
      threshold: 80,
      color: 'pink'
    },
    {
      id: 'complete',
      name: 'Profile Master',
      description: 'Your profile is 100% complete!',
      icon: '🏆',
      threshold: 100,
      color: 'pink'
    }
  ];

  useEffect(() => {
    // Show celebration when completion increases
    if (completionPercentage > previousCompletion) {
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 2000);
    }
    setPreviousCompletion(completionPercentage);
  }, [completionPercentage, previousCompletion]);

  const earnedBadges = badges.filter(badge => completionPercentage >= badge.threshold);
  const nextBadge = badges.find(badge => completionPercentage < badge.threshold);

  const getProgressColor = () => {
    if (completionPercentage >= 100) return 'from-pink-400 to-pink-600';
    if (completionPercentage >= 80) return 'from-pink-300 to-pink-500';
    if (completionPercentage >= 50) return 'from-pink-200 to-pink-400';
    return 'from-gray-200 to-gray-300';
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-pink-100">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Profile Progress</h3>
        <div className="text-sm text-gray-500">
          {completedSections.length} of {totalSections} sections
        </div>
      </div>

      {/* Progress Circle */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative">
          <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="url(#gradient)"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray={`${2 * Math.PI * 45}`}
              strokeDashoffset={`${2 * Math.PI * 45 * (1 - completionPercentage / 100)}`}
              className="transition-all duration-1000 ease-out"
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#f472b6" />
                <stop offset="100%" stopColor="#ec4899" />
              </linearGradient>
            </defs>
          </svg>
          
          {/* Percentage text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className={`text-2xl font-bold ${showCelebration ? 'animate-bounce' : ''} text-gray-900`}>
                {completionPercentage}%
              </div>
              <div className="text-xs text-gray-500">Complete</div>
            </div>
          </div>
        </div>
      </div>

      {/* Celebration Message */}
      {showCelebration && (
        <div className="mb-4 p-3 bg-pink-50 border border-pink-200 rounded-lg animate-fadeDown">
          <div className="flex items-center space-x-2">
            <span className="text-pink-600 animate-bounce">🎉</span>
            <span className="text-sm font-medium text-pink-800">Great job! Keep going!</span>
          </div>
        </div>
      )}

      {/* Earned Badges */}
      {earnedBadges.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Earned Badges</h4>
          <div className="grid grid-cols-2 gap-2">
            {earnedBadges.map((badge, index) => (
              <div
                key={badge.id}
                className={`
                  p-3 rounded-lg border-2 border-pink-200 bg-pink-50 transition-all duration-300
                  ${showCelebration && index === earnedBadges.length - 1 ? 'animate-pulse' : ''}
                `}
              >
                <div className="text-center">
                  <div className="text-2xl mb-1">{badge.icon}</div>
                  <div className="text-xs font-medium text-pink-800">{badge.name}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Badge */}
      {nextBadge && completionPercentage < 100 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Next Reward</h4>
          <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="text-2xl opacity-50">{nextBadge.icon}</div>
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{nextBadge.name}</div>
                <div className="text-xs text-gray-500">{nextBadge.description}</div>
                <div className="text-xs text-pink-600 mt-1">
                  {nextBadge.threshold - completionPercentage}% to go
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="space-y-2">
        {completionPercentage < 100 && (
          <button className="w-full px-4 py-2 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors duration-200 text-sm">
            Continue Profile Setup
          </button>
        )}
        
        {completionPercentage >= 50 && (
          <button className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors duration-200 text-sm">
            Find Grant Matches
          </button>
        )}
      </div>

      {/* Tips */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-xs text-gray-600">
          <span className="font-medium">💡 Tip:</span> 
          {completionPercentage < 50 
            ? ' Complete more sections to unlock better grant matches.'
            : completionPercentage < 100
            ? ' Finish your profile for the most accurate recommendations.'
            : ' Your complete profile helps us find the best grants for you!'
          }
        </div>
      </div>
    </div>
  );
};

export default ProfileRewards;