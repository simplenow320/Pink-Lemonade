import axios from 'axios';

// Use environment variable for API base URL, with fallback to relative path for local development
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

/**
 * Custom error class for API errors that includes user-friendly messages
 */
export class ApiError extends Error {
  constructor(message, status, originalError = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.originalError = originalError;
  }
}

/**
 * Transforms an error response into a user-friendly message
 * @param {Error} error - The error object from Axios
 * @returns {string} A user-friendly error message
 */
export const getUserFriendlyErrorMessage = (error) => {
  // If it's already an ApiError, just return its message
  if (error instanceof ApiError) {
    return error.message;
  }

  // Handle axios error responses
  if (error.response) {
    const { status } = error.response;
    
    // Handle specific HTTP status codes
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 500:
        return 'A server error occurred. Our team has been notified.';
      default:
        return `An error occurred (Status: ${status}). Please try again later.`;
    }
  }

  // Handle network errors
  if (error.request && !error.response) {
    return 'Unable to connect to the server. Please check your internet connection.';
  }

  // Handle other errors
  return 'An unexpected error occurred. Please try again later.';
};

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add reasonable timeouts
  timeout: 30000, // 30 seconds
});

// Handle errors with improved logging and error transformation
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Create a more structured log
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });

    // Transform to ApiError with user-friendly message
    const userMessage = getUserFriendlyErrorMessage(error);
    const status = error.response?.status || 0;
    
    return Promise.reject(new ApiError(userMessage, status, error));
  }
);

// Grant APIs
export const getGrants = async (filters = {}) => {
  const { status, sortBy, sortDir } = filters;
  let url = '/grants';
  
  // Add query parameters if provided
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (sortBy) params.append('sort_by', sortBy);
  if (sortDir) params.append('sort_dir', sortDir);
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  
  const response = await api.get(url);
  return response.data;
};

export const getGrant = async (id) => {
  const response = await api.get(`/grants/${id}`);
  return response.data;
};

export const createGrant = async (grantData) => {
  const response = await api.post('/grants', grantData);
  return response.data;
};

export const updateGrant = async (id, grantData) => {
  const response = await api.put(`/grants/${id}`, grantData);
  return response.data;
};

export const deleteGrant = async (id) => {
  const response = await api.delete(`/grants/${id}`);
  return response.data;
};

export const getDashboardData = async () => {
  const response = await api.get('/grants/dashboard');
  return response.data;
};

export const uploadGrantFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/grants/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 seconds for file uploads
    });
    
    return response.data;
  } catch (error) {
    // Create a more structured log
    console.error('File Upload Error:', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      error: error.message,
    });

    // Transform to ApiError with user-friendly message
    const userMessage = getUserFriendlyErrorMessage(error);
    const status = error.response?.status || 0;
    
    throw new ApiError(userMessage, status, error);
  }
};

export const processGrantUrl = async (url) => {
  const response = await api.post('/grants/url', { url });
  return response.data;
};

// Organization APIs
export const getOrganization = async () => {
  const response = await api.get('/organization');
  return response.data;
};

export const updateOrganization = async (orgData) => {
  const response = await api.put('/organization', orgData);
  return response.data;
};

export const seedOrganization = async () => {
  const response = await api.post('/organization/seed');
  return response.data;
};

// Scraper APIs
export const getScraperSources = async () => {
  const response = await api.get('/scraper/sources');
  return response.data;
};

export const addScraperSource = async (sourceData) => {
  const response = await api.post('/scraper/sources', sourceData);
  return response.data;
};

export const updateScraperSource = async (id, sourceData) => {
  const response = await api.put(`/scraper/sources/${id}`, sourceData);
  return response.data;
};

export const deleteScraperSource = async (id) => {
  const response = await api.delete(`/scraper/sources/${id}`);
  return response.data;
};

export const runScraper = async () => {
  const response = await api.post('/scraper/run');
  return response.data;
};

export const getScraperHistory = async (limit = 10) => {
  const response = await api.get(`/scraper/history?limit=${limit}`);
  return response.data;
};

export const initializeScraperSources = async () => {
  const response = await api.post('/scraper/initialize-sources');
  return response.data;
};

// AI APIs
export const matchGrant = async (grantId) => {
  const response = await api.post('/ai/match', { grant_id: grantId });
  return response.data;
};

export const generateNarrative = async (grantId, caseForSupport = null) => {
  const data = { grant_id: grantId };
  if (caseForSupport) {
    data.case_for_support = caseForSupport;
  }
  
  const response = await api.post('/ai/generate-narrative', data);
  return response.data;
};

export const getNarrative = async (grantId) => {
  const response = await api.get(`/ai/narratives/${grantId}`);
  return response.data;
};

export const updateNarrative = async (narrativeId, content) => {
  const response = await api.put(`/ai/narratives/${narrativeId}`, { content });
  return response.data;
};

export const extractFromText = async (text) => {
  const response = await api.post('/ai/extract-from-text', { text });
  return response.data;
};

export const extractFromUrl = async (url) => {
  const response = await api.post('/ai/extract-from-url', { url });
  return response.data;
};

// Application initialization
export const initializeOrganization = async () => {
  try {
    // First try to get the organization
    const response = await api.get('/organization');
    return response.data;
  } catch (error) {
    // If organization doesn't exist, try to seed it
    if (error.response && error.response.status === 404) {
      const seedResponse = await api.post('/organization/seed');
      return seedResponse.data;
    }
    throw error;
  }
};

// Analytics APIs
export const getAnalyticsSuccessMetrics = async (period = 'all', limit = null, includeCategories = true) => {
  let url = '/analytics/success-metrics';
  
  // Add query parameters
  const params = new URLSearchParams();
  params.append('period', period);
  if (limit) params.append('limit', limit);
  params.append('include_categories', includeCategories.toString());
  
  url += `?${params.toString()}`;
  
  const response = await api.get(url);
  return response.data;
};

export const getAnalyticsTrends = async (metric = 'success_rate', period = 'monthly', months = 12) => {
  const url = `/analytics/trends?metric=${metric}&period=${period}&months=${months}`;
  const response = await api.get(url);
  return response.data;
};

export const getAnalyticsCategoryComparison = async () => {
  const response = await api.get('/analytics/category-comparison');
  return response.data;
};

export const getAnalyticsGrantTimeline = async (grantId) => {
  const response = await api.get(`/analytics/grant-timeline/${grantId}`);
  return response.data;
};

export const getAnalyticsOverview = async () => {
  const response = await api.get('/analytics/overview');
  return response.data;
};

export const updateAnalyticsMetrics = async () => {
  const response = await api.post('/analytics/update-metrics');
  return response.data;
};

// Writing Assistant APIs
export const getWritingAssistantSections = async () => {
  const response = await api.get('/writing-assistant/sections');
  return response.data;
};

export const generateWritingSection = async (sectionType, grantId, additionalInputs = {}) => {
  const data = {
    section_type: sectionType,
    grant_id: grantId
  };
  
  if (Object.keys(additionalInputs).length > 0) {
    data.additional_inputs = additionalInputs;
  }
  
  const response = await api.post('/writing-assistant/generate', data);
  return response.data;
};

export const improveWritingSection = async (sectionType, content, feedback) => {
  const data = {
    section_type: sectionType,
    content,
    feedback
  };
  
  const response = await api.post('/writing-assistant/improve', data);
  return response.data;
};

export const generateSectionOutline = async (sectionType, grantId) => {
  const data = {
    section_type: sectionType,
    grant_id: grantId
  };
  
  const response = await api.post('/writing-assistant/outline', data);
  return response.data;
};

// Export the api object as default for direct axios calls
export default api;
