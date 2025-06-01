/**
 * Utility for preloading critical images.
 */

const preloadedImages = new Set();

/**
 * Preload an image and return a promise that resolves when the image is loaded.
 * @param {string} src - The image source URL
 * @returns {Promise} A promise that resolves when the image is loaded
 */
export const preloadImage = (src) => {
  if (preloadedImages.has(src)) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      preloadedImages.add(src);
      resolve();
    };
    img.onerror = reject;
    img.src = src;
  });
};

/**
 * Preload multiple images in parallel.
 * @param {string[]} sources - Array of image source URLs
 * @returns {Promise} A promise that resolves when all images are loaded
 */
export const preloadImages = (sources) => {
  return Promise.all(sources.map(src => preloadImage(src)));
};

/**
 * Preload critical images for a user profile.
 * @param {Object} user - The user object containing image URLs
 * @returns {Promise} A promise that resolves when all critical images are loaded
 */
export const preloadUserImages = (user) => {
  const criticalImages = [
    user.profileImageUrl && `/api/storage/profile_pics/${user.profileImageUrl}`,
    '/static/default_profile.jpg',
    '/static/default_face.jpg'
  ].filter(Boolean);

  return preloadImages(criticalImages);
}; 