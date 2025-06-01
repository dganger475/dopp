// MatchCard.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './SearchResult.module.css';

// --- The unified MatchCard component ---
const SearchResult = ({ result, index, hideSimilarity = false }) => {
  const navigate = useNavigate();

  // Extract data from the unified card structure
  const {
    id,
    image,
    username,
    label,
    similarity,
    stateDecade,
    is_registered
  } = result;

  const handleCardClick = () => {
    // Only navigate for non-registered users
    if (!is_registered) {
      // Navigate to comparison page with match data
      navigate(`/comparison/${id || index}`, {
        state: {
          matchData: result,
          // We'll get user data from the API in the comparison page
        }
      });
    }
  };
  
  // Card styling based on user type
  const cardBgColor = is_registered ? '#ffffff' : 'rgb(0, 123, 255)'; // White for registered, blue for unclaimed
  const borderColor = is_registered ? '#e0e0e0' : '#000000'; // Light grey border for registered, black for unclaimed
  const labelBgColor = is_registered ? '#e0e0e0' : '#000000'; // Light grey label for registered, black for unclaimed
  const labelTextColor = is_registered ? '#000000' : 'rgb(255, 255, 255)'; // Black text for registered, white for unclaimed
  
  // Fallback for image
  const displayImage = image || '/static/images/default_profile.svg';

  // Fallback for similarity
  let displaySimilarity = '';
  let percent = null;
  if (similarity !== undefined && similarity !== null && similarity !== '') {
    const num = parseFloat(String(similarity).replace('%', ''));
    if (!isNaN(num)) {
      percent = num <= 1 ? Math.round(num * 100) : Math.round(num);
      displaySimilarity = `${percent}%`;
    } else {
      displaySimilarity = '--%';
    }
  } else {
    displaySimilarity = '--%';
  }

  return (
    <div 
      className={styles.card} 
      onClick={handleCardClick}
      style={{
        backgroundColor: cardBgColor,
        borderColor: borderColor,
        cursor: is_registered ? 'default' : 'pointer'
      }}
    >
      <div className={styles.imageContainer}>
        <img 
          src={displayImage} 
          alt={username} 
          className={styles.image}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = '/static/images/default_profile.svg';
          }}
        />
      </div>
      <div className={styles.details}>
        <div 
          className={styles.label}
          style={{
            backgroundColor: labelBgColor,
            color: labelTextColor
          }}
        >
          {label}
        </div>
        <div className={styles.username}>{username}</div>
        {/* Similarity only if not hidden */}
        {!hideSimilarity && displaySimilarity && (
          <div className={styles.similarity}>{displaySimilarity}</div>
        )}
        {stateDecade && (
          <div className={styles.location}>{stateDecade}</div>
        )}
      </div>
    </div>
  );
};

export default SearchResult;