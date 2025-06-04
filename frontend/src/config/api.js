// Base URL for API requests - dynamically determined
const API_BASE_URL = 'https://dopple503.fly.dev';

// Helper function to build API URLs with proper handling
export const getApiUrl = (path) => {
  // Make sure path starts with a slash if not already
  const formattedPath = path.startsWith('/') ? path : `/${path}`;
  
  // If we're in development or on the same domain, use relative URLs
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return formattedPath;
  }
  
  // In production, always use the full URL
  return `${API_BASE_URL}${formattedPath}`;
};

export default API_BASE_URL;
