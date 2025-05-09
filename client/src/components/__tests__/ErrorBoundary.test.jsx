import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

// Create a component that throws an error when rendered
const ErrorComponent = () => {
  throw new Error('Test error');
};

// Suppress console errors for cleaner test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('ErrorBoundary', () => {
  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">Child content</div>
      </ErrorBoundary>
    );
    
    expect(screen.getByTestId('child')).toBeInTheDocument();
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });
  
  test('renders fallback UI when an error occurs', () => {
    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>
    );
    
    // Check if the error message is displayed
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/Test error/i)).toBeInTheDocument();
    
    // Check if the "View Error Details" is present
    expect(screen.getByText(/View Error Details/i)).toBeInTheDocument();
    
    // Check if the reset button is present
    expect(screen.getByText(/Back to Home/i)).toBeInTheDocument();
  });
  
  test('calls custom resetAction when reset button is clicked', () => {
    const resetAction = jest.fn();
    
    render(
      <ErrorBoundary resetAction={resetAction} resetButtonText="Try again">
        <ErrorComponent />
      </ErrorBoundary>
    );
    
    // Check if the custom button text is displayed
    expect(screen.getByText(/Try again/i)).toBeInTheDocument();
    
    // Click the reset button
    fireEvent.click(screen.getByText(/Try again/i));
    
    // Check if resetAction was called
    expect(resetAction).toHaveBeenCalledTimes(1);
  });
  
  test('uses custom fallback render prop if provided', () => {
    const customFallback = (error) => (
      <div data-testid="custom-fallback">
        Custom error: {error.message}
      </div>
    );
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ErrorComponent />
      </ErrorBoundary>
    );
    
    // Check if the custom fallback is rendered
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText(/Custom error: Test error/i)).toBeInTheDocument();
  });
});