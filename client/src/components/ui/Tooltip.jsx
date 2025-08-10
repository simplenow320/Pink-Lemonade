import React, { useState } from 'react';

const Tooltip = ({ 
  children, 
  content, 
  position = 'top',
  size = 'medium',
  delay = 200,
  interactive = false 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showTimeout, setShowTimeout] = useState(null);
  const [hideTimeout, setHideTimeout] = useState(null);

  const handleMouseEnter = () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      setHideTimeout(null);
    }
    
    const timeout = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setShowTimeout(timeout);
  };

  const handleMouseLeave = () => {
    if (showTimeout) {
      clearTimeout(showTimeout);
      setShowTimeout(null);
    }
    
    if (!interactive) {
      const timeout = setTimeout(() => {
        setIsVisible(false);
      }, 100);
      setHideTimeout(timeout);
    }
  };

  const handleTooltipEnter = () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      setHideTimeout(null);
    }
  };

  const handleTooltipLeave = () => {
    const timeout = setTimeout(() => {
      setIsVisible(false);
    }, 100);
    setHideTimeout(timeout);
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top':
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
      case 'bottom':
        return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
      default:
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    }
  };

  const getArrowClasses = () => {
    switch (position) {
      case 'top':
        return 'top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-800';
      case 'bottom':
        return 'bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-800';
      case 'left':
        return 'left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-800';
      case 'right':
        return 'right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-800';
      default:
        return 'top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-800';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'max-w-xs text-xs px-2 py-1';
      case 'large':
        return 'max-w-sm text-sm px-4 py-3';
      default:
        return 'max-w-xs text-sm px-3 py-2';
    }
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="cursor-help"
      >
        {children}
      </div>
      
      {isVisible && (
        <div
          className={`
            absolute z-50 ${getPositionClasses()}
            transition-all duration-200 ease-out
            ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
          `}
          onMouseEnter={interactive ? handleTooltipEnter : undefined}
          onMouseLeave={interactive ? handleTooltipLeave : undefined}
        >
          {/* Tooltip Content */}
          <div className={`
            bg-gray-800 text-white rounded-lg shadow-lg
            ${getSizeClasses()}
            animate-fadeDown
          `}>
            {typeof content === 'string' ? (
              <div dangerouslySetInnerHTML={{ __html: content }} />
            ) : (
              content
            )}
          </div>
          
          {/* Arrow */}
          <div className={`
            absolute w-0 h-0 border-4 ${getArrowClasses()}
          `}></div>
        </div>
      )}
    </div>
  );
};

// Helper component for form field tooltips
export const FieldTooltip = ({ label, description, example, required = false }) => {
  const content = (
    <div>
      <div className="font-medium text-white mb-1">{label}</div>
      <div className="text-gray-300 text-xs mb-2">{description}</div>
      {example && (
        <div className="text-pink-200 text-xs italic">
          Example: {example}
        </div>
      )}
      {required && (
        <div className="text-pink-300 text-xs mt-1">* Required field</div>
      )}
    </div>
  );

  return (
    <Tooltip content={content} size="large" interactive={true}>
      <svg className="w-4 h-4 text-gray-400 hover:text-pink-500 transition-colors duration-200 cursor-help" 
           fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </Tooltip>
  );
};

export default Tooltip;