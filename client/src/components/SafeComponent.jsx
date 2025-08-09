import React from 'react';
import PropTypes from 'prop-types';
import ErrorBoundary from './ErrorBoundary';

/**
 * A wrapper component that provides error handling for any component.
 * This is a convenient way to wrap components in an ErrorBoundary with
 * consistent styling and behavior.
 *
 * @param {Object} props - The component props
 * @param {React.ReactNode} props.children - The child components to render
 * @param {string} props.fallbackTitle - Optional custom title for the error fallback
 * @param {string} props.resetButtonText - Optional custom text for the reset button
 * @param {Function} props.onError - Optional function to call when an error occurs
 * @param {Function} props.resetAction - Optional function to call when reset button is clicked
 */
const SafeComponent = ({
  children,
  fallbackTitle = 'Something went wrong',
  resetButtonText = 'Try again',
  onError,
  resetAction,
}) => {
  const customFallback = (error) => (
    <div className="bg-white shadow-md rounded-lg p-6 my-4">
      <div className="flex items-center mb-4">
        <svg
          className="w-6 h-6 text-red-500 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="text-lg font-semibold text-gray-800">{fallbackTitle}</h3>
      </div>

      <p className="text-red-600 mb-4">{error.message}</p>

      <button
        onClick={resetAction || (() => window.location.reload())}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        {resetButtonText}
      </button>
    </div>
  );

  return (
    <ErrorBoundary fallback={customFallback} onError={onError} resetAction={resetAction}>
      {children}
    </ErrorBoundary>
  );
};

SafeComponent.propTypes = {
  children: PropTypes.node.isRequired,
  fallbackTitle: PropTypes.string,
  resetButtonText: PropTypes.string,
  onError: PropTypes.func,
  resetAction: PropTypes.func,
};

export default SafeComponent;
