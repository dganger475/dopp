// Base URL for API requests - dynamically determined
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? '' // Use relative URLs in development
  : window.location.hostname.includes('ngrok-free.app')
    ? `https://${window.location.hostname}`
    : window.location.origin;

// Helper function to build API URLs with proper handling
export const getApiUrl = (path) => {
  // Make sure path starts with a slash if not already
  const formattedPath = path.startsWith('/') ? path : `/${path}`;
  
  // If we're in development or on the same domain, use relative URLs
  if (!API_BASE_URL || window.location.origin === API_BASE_URL) {
    return formattedPath;
  }
  return `${API_BASE_URL}${formattedPath}`;
};

export default API_BASE_URL;
