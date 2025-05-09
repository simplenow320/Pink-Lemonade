// Add any global Jest setup here

// Mock process.env for tests
process.env.REACT_APP_API_URL = 'http://localhost:5000/api';

// Suppress console errors in tests
global.console.error = jest.fn();

// Add any global mocks here if needed
// For example, we can mock fetch or other browser APIs