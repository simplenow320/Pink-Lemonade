import React from 'react';

const ProgressIndicator = ({ currentStep = 1, totalSteps = 5, stepLabels = [] }) => {
  const defaultLabels = [
    'Basic Info',
    'Programs',
    'Capacity', 
    'Grant History',
    'AI Learning'
  ];

  const labels = stepLabels.length ? stepLabels : defaultLabels;

  return (
    <div className="w-full max-w-4xl mx-auto py-6">
      {/* Main Progress Bar */}
      <div className="relative mb-8">
        <div className="absolute top-4 left-0 w-full h-0.5 bg-gray-200"></div>
        <div 
          className="absolute top-4 left-0 h-0.5 bg-gradient-to-r from-pink-400 to-pink-600 transition-all duration-500 ease-out"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        ></div>
        
        {/* Step Circles */}
        <div className="relative flex justify-between">
          {Array.from({ length: totalSteps }, (_, index) => {
            const stepNumber = index + 1;
            const isCompleted = stepNumber < currentStep;
            const isCurrent = stepNumber === currentStep;
            
            return (
              <div key={stepNumber} className="flex flex-col items-center">
                <div
                  className={`
                    w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-medium transition-all duration-300
                    ${isCompleted 
                      ? 'bg-pink-500 border-pink-500 text-white animate-pulse' 
                      : isCurrent
                      ? 'bg-white border-pink-500 text-pink-500 shadow-lg scale-110' 
                      : 'bg-gray-50 border-gray-300 text-gray-400'
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    stepNumber
                  )}
                </div>
                
                {/* Step Label */}
                <div className="mt-2 text-center">
                  <div 
                    className={`
                      text-xs font-medium transition-colors duration-300
                      ${isCurrent ? 'text-pink-600' : isCompleted ? 'text-gray-700' : 'text-gray-400'}
                    `}
                  >
                    {labels[index]}
                  </div>
                  {isCurrent && (
                    <div className="text-xs text-gray-500 mt-1">Current Step</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Progress Text */}
      <div className="text-center">
        <div className="text-sm text-gray-600">
          Step {currentStep} of {totalSteps}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div 
            className="bg-gradient-to-r from-pink-400 to-pink-600 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {Math.round((currentStep / totalSteps) * 100)}% Complete
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;