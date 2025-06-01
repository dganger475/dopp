/**
 * Image URL utilities for handling B2 image URLs in React components.
 */

/**
 * Get the URL for a face image.
 * @param {string} filename - The face image filename
 * @returns {string} The URL for the image
 */
export const getFaceImageUrl = (filename) => {
  if (!filename) {
    return '/static/default_face.jpg';
  }

  // Verify it's an anonymized filename
  if (!isAnonymizedFaceFilename(filename)) {
    console.warn(`Invalid face filename format: ${filename}`);
    return '/static/default_face.jpg';
  }

  // Get URL from storage backend
  return `/api/storage/faces/${filename}`;
};

/**
 * Get the URL for a profile image.
 * @param {string} filename - The profile image filename
 * @returns {string} The URL for the image
 */
export const getProfileImageUrl = (filename) => {
  if (!filename) {
    return '/static/default_profile.jpg';
  }

  // Get URL from storage backend
  return `/api/storage/profile_pics/${filename}`;
};

/**
 * Check if a filename follows the anonymized face format.
 * @param {string} filename - The filename to check
 * @returns {boolean} True if the filename matches the format 'face_000123.jpg'
 */
export const isAnonymizedFaceFilename = (filename) => {
  return /^face_\d{6}\.jpg$/.test(filename);
};

/**
 * Extract the face ID from an anonymized filename.
 * @param {string} filename - The filename to parse (e.g., 'face_000123.jpg')
 * @returns {number|null} The face ID if valid, null otherwise
 */
export const parseFaceIdFromFilename = (filename) => {
  const match = filename.match(/^face_(\d{6})\.jpg$/);
  return match ? parseInt(match[1], 10) : null;
};

/**
 * Generate an anonymized filename for a face image.
 * @param {number} faceId - The ID of the face in the database
 * @returns {string} Filename in format 'face_000123.jpg'
 */
export const generateFaceFilename = (faceId) => {
  return `face_${faceId.toString().padStart(6, '0')}.jpg`;
}; 