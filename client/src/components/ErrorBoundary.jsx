import React from 'react';
import PropTypes from 'prop-types';

/**
 * A component that catches JavaScript errors anywhere in its child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the app.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to the console
    console.error('ErrorBoundary caught an error', error, errorInfo);
    this.setState({ errorInfo });

    // You can also log the error to an error reporting service like Sentry here
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      // You can customize the fallback UI here
      return this.props.fallback ? (
        this.props.fallback(this.state.error, this.state.errorInfo)
      ) : (
        <div className="error-boundary">
          <div className="error-container bg-red-50 border border-red-200 rounded-lg p-6 mt-4 mx-auto max-w-5xl">
            <h2 className="text-red-700 text-xl font-semibold mb-3">Something went wrong</h2>
            <p className="text-red-600 mb-4">{this.state.error && this.state.error.toString()}</p>
            <div className="bg-white p-4 rounded border border-red-100 mb-4 overflow-auto max-h-60">
              <details className="text-sm text-gray-700">
                <summary className="cursor-pointer font-medium text-gray-900 mb-2">
                  View Error Details
                </summary>
                <pre className="mt-2 whitespace-pre-wrap font-mono text-xs">
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            </div>
            <button
              onClick={() => {
                // Reset the error state
                this.setState({ hasError: false, error: null, errorInfo: null });
                // Try to reload or navigate back
                if (this.props.resetAction) {
                  this.props.resetAction();
                } else {
                  window.location.href = '/';
                }
              }}
              className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded transition-colors"
            >
              {this.props.resetButtonText || 'Back to Home'}
            </button>
          </div>
        </div>
      );
    }

    // If there's no error, render the children
    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.func,
  onError: PropTypes.func,
  resetAction: PropTypes.func,
  resetButtonText: PropTypes.string,
};

export default ErrorBoundary;
