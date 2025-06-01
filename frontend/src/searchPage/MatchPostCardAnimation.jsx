import React from 'react';
import styles from './MatchPostCardAnimation.module.css';
import API_BASE_URL from '../config/api';

// Helper function to get match badge color based on percentage
const getMatchColor = (similarity) => {
  const percent = parseFloat(similarity) * 100;
  
  if (percent >= 90) return '#22c55e'; // Green for high matches
  if (percent >= 70) return '#3b82f6'; // Blue for good matches
  if (percent >= 50) return '#f59e0b'; // Yellow/amber for medium matches
  return '#ef4444'; // Red for low matches
};

const MatchPostCardAnimation = ({
  userImage,
  matchImage,
  similarity,
  username,
  matchId,
  decade,
  state,
  isAnimating
}) => {
  // Format similarity as a percentage
  let similarityPercentage = Number(similarity);
  if (similarityPercentage > 1) {
    similarityPercentage = similarityPercentage / 100;
  }
  similarityPercentage = Math.round(similarityPercentage * 100);
  const matchColor = getMatchColor(similarityPercentage / 100);

  return (
    <div className={`${styles.matchCard} ${isAnimating ? styles.animating : ''}`}>
      <div className={styles.cardContent}>
        {/* User Image */}
        <div className={styles.userImageSection}>
          {userImage ? (
            <img
              src={userImage.startsWith('http') ? userImage : `${API_BASE_URL}${userImage}`}
              alt="User"
              className={styles.userImage}
            />
          ) : (
            <div className={styles.fallbackImage}>
              {username ? username[0].toUpperCase() : 'U'}
            </div>
          )}
        </div>

        {/* Match ID and Similarity Score */}
        <div className={styles.matchInfo}>
          <div className={styles.matchId}>
            ID: {matchId || 'Unknown'}
          </div>
          <div 
            className={styles.similarityScore}
            style={{ color: matchColor }}
          >
            {similarityPercentage}%
          </div>
        </div>

        {/* Match Details */}
        <div className={styles.matchDetails}>
          {state && (
            <div className={styles.matchInfo}>
              {state}
            </div>
          )}
          {decade && (
            <div className={styles.matchInfo}>
              {decade}s
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatchPostCardAnimation;
