import { ApiError, getUserFriendlyErrorMessage } from '../api';

describe('ApiError class', () => {
  test('creates an instance with the correct properties', () => {
    const message = 'Test error message';
    const status = 404;
    const originalError = new Error('Original error');
    
    const apiError = new ApiError(message, status, originalError);
    
    expect(apiError.message).toBe(message);
    expect(apiError.name).toBe('ApiError');
    expect(apiError.status).toBe(status);
    expect(apiError.originalError).toBe(originalError);
  });
});

describe('getUserFriendlyErrorMessage', () => {
  test('returns the original message for ApiError instances', () => {
    const message = 'Friendly error message';
    const apiError = new ApiError(message, 500);
    
    expect(getUserFriendlyErrorMessage(apiError)).toBe(message);
  });
  
  test('returns appropriate message for 400 status error', () => {
    const error = { 
      response: { status: 400 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('Invalid request. Please check your input and try again.');
  });
  
  test('returns appropriate message for 401 status error', () => {
    const error = { 
      response: { status: 401 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('Authentication required. Please log in again.');
  });
  
  test('returns appropriate message for 403 status error', () => {
    const error = { 
      response: { status: 403 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('You do not have permission to perform this action.');
  });
  
  test('returns appropriate message for 404 status error', () => {
    const error = { 
      response: { status: 404 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('The requested resource was not found.');
  });
  
  test('returns appropriate message for 500 status error', () => {
    const error = { 
      response: { status: 500 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('A server error occurred. Our team has been notified.');
  });
  
  test('returns generic message for other status codes', () => {
    const error = { 
      response: { status: 503 }
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('An error occurred (Status: 503). Please try again later.');
  });
  
  test('returns network error message for request with no response', () => {
    const error = { 
      request: {}, 
      response: undefined
    };
    
    expect(getUserFriendlyErrorMessage(error)).toBe('Unable to connect to the server. Please check your internet connection.');
  });
  
  test('returns generic error message for other errors', () => {
    const error = new Error('Unknown error');
    
    expect(getUserFriendlyErrorMessage(error)).toBe('An unexpected error occurred. Please try again later.');
  });
});