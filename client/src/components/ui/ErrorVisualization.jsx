import React, { useState } from 'react';

const ErrorVisualization = ({ 
  error, 
  type = 'validation', 
  field = '', 
  solution = '',
  onRetry = null 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Error type configurations
  const errorTypes = {
    validation: {
      icon: '⚠️',
      color: 'yellow',
      title: 'Input Needs Fixing'
    },
    network: {
      icon: '📡',
      color: 'blue',
      title: 'Connection Problem'
    },
    permission: {
      icon: '🔒',
      color: 'red',
      title: 'Access Denied'
    },
    server: {
      icon: '🔧',
      color: 'orange',
      title: 'System Issue'
    },
    format: {
      icon: '📝',
      color: 'purple',
      title: 'Format Problem'
    }
  };

  const config = errorTypes[type] || errorTypes.validation;

  // Generate simple explanation based on error type
  const getSimpleExplanation = () => {
    switch (type) {
      case 'validation':
        return `The ${field || 'information'} you entered doesn't match what we need.`;
      case 'network':
        return 'We cannot connect to our servers right now.';
      case 'permission':
        return 'You do not have permission to do this action.';
      case 'server':
        return 'Our system is having trouble. This is not your fault.';
      case 'format':
        return `The ${field || 'format'} is not correct.`;
      default:
        return 'Something went wrong.';
    }
  };

  // Get visual diagram based on error type
  const getVisualDiagram = () => {
    switch (type) {
      case 'validation':
        return (
          <div className="flex items-center space-x-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.96-.833-2.732 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-yellow-800">Check Your Input</div>
              <div className="text-xs text-yellow-700 mt-1">
                {field && `Look at the "${field}" field again`}
              </div>
            </div>
          </div>
        );
      
      case 'network':
        return (
          <div className="flex items-center space-x-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600">💻</span>
              </div>
              <div className="text-blue-600">→</div>
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center animate-pulse">
                <span className="text-red-600">❌</span>
              </div>
              <div className="text-blue-600">→</div>
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-gray-600">🏢</span>
              </div>
            </div>
          </div>
        );

      case 'format':
        return (
          <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-xs text-purple-700 font-medium mb-2">What You Entered</div>
                <div className="p-2 bg-red-100 rounded border border-red-200 text-red-700 text-sm">
                  ❌ Wrong format
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-purple-700 font-medium mb-2">What We Need</div>
                <div className="p-2 bg-green-100 rounded border border-green-200 text-green-700 text-sm">
                  ✅ Right format
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-center text-gray-600">
              <div className="text-2xl mb-2">{config.icon}</div>
              <div className="text-sm">{config.title}</div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="bg-white border-l-4 border-pink-400 rounded-lg shadow-sm p-4 animate-fadeDown">
      {/* Header */}
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-10 h-10 bg-pink-100 rounded-full flex items-center justify-center">
            <span className="text-lg">{config.icon}</span>
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-medium text-gray-900">{config.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{getSimpleExplanation()}</p>
          
          {/* Original error message (if expanded) */}
          {isExpanded && error && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 font-medium mb-1">Technical Details:</div>
              <div className="text-xs text-gray-700 font-mono">{error}</div>
            </div>
          )}
        </div>

        {/* Expand button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors duration-200"
        >
          <svg 
            className={`w-5 h-5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Visual Diagram */}
      <div className="mt-4">
        {getVisualDiagram()}
      </div>

      {/* Solution */}
      {solution && (
        <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-start space-x-2">
            <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="text-sm font-medium text-green-800">How to Fix This</div>
              <div className="text-sm text-green-700 mt-1">{solution}</div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors duration-200 text-sm"
          >
            Try Again
          </button>
        )}
        
        {type === 'validation' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors duration-200 text-sm"
          >
            Need Help?
          </button>
        )}
      </div>
    </div>
  );
};

// Helper component for common error scenarios
export const FormValidationError = ({ field, value, expected, onFix }) => (
  <ErrorVisualization
    type="validation"
    field={field}
    error={`Invalid ${field}: ${value}`}
    solution={`Enter ${expected}. Look for the format example above the field.`}
    onRetry={onFix}
  />
);

export const NetworkError = ({ onRetry }) => (
  <ErrorVisualization
    type="network"
    error="Network connection failed"
    solution="Check your internet connection and try again. If this keeps happening, wait a few minutes."
    onRetry={onRetry}
  />
);

export const ServerError = ({ onRetry }) => (
  <ErrorVisualization
    type="server"
    error="Internal server error"
    solution="Our team has been notified. Please try again in a few minutes."
    onRetry={onRetry}
  />
);

export default ErrorVisualization;