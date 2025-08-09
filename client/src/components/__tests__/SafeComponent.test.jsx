import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SafeComponent from '../SafeComponent';

// A component that throws an error
const ErrorComponent = () => {
  throw new Error('Test error in SafeComponent');
};

// Suppress console errors during tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('SafeComponent', () => {
  test('renders children when there is no error', () => {
    render(
      <SafeComponent>
        <div data-testid="safe-child">Safe Content</div>
      </SafeComponent>
    );

    expect(screen.getByTestId('safe-child')).toBeInTheDocument();
    expect(screen.getByText('Safe Content')).toBeInTheDocument();
  });

  test('renders custom fallback UI when an error occurs', () => {
    render(
      <SafeComponent fallbackTitle="Custom Error Title" resetButtonText="Reset Test">
        <ErrorComponent />
      </SafeComponent>
    );

    // Check if the custom fallback elements are shown
    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    expect(screen.getByText('Test error in SafeComponent')).toBeInTheDocument();
    expect(screen.getByText('Reset Test')).toBeInTheDocument();
  });

  test('calls custom resetAction when reset button is clicked', () => {
    const resetAction = jest.fn();

    render(
      <SafeComponent resetAction={resetAction}>
        <ErrorComponent />
      </SafeComponent>
    );

    // Click the reset button
    fireEvent.click(screen.getByText('Try again'));

    // Verify resetAction was called
    expect(resetAction).toHaveBeenCalledTimes(1);
  });

  test('calls onError when an error occurs', () => {
    const onError = jest.fn();

    render(
      <SafeComponent onError={onError}>
        <ErrorComponent />
      </SafeComponent>
    );

    // Verify onError was called with an error
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error);
    expect(onError.mock.calls[0][0].message).toBe('Test error in SafeComponent');
  });
});
