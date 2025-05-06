import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
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
  
  const response = await axios.post('/api/grants/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
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
