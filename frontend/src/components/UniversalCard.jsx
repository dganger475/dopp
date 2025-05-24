import React, { useState } from 'react';
import styles from './UniversalCard.module.css';

const UniversalCard = ({
  image,
  username,
  // city, // Add if you have city data for currentUser
  decade,
  state,
  similarity,
  cardType = 'registeredMatch', // Default to registered (red card)
  style = {}
}) => {
  let labelText = '';
  let specificCardClass = '';

  switch (cardType) {
    case 'currentUser':
      labelText = 'YOUR CARD';
      specificCardClass = styles.currentUserCard;
      break;
    case 'unregisteredMatch':
      labelText = 'UNCLAIMED PROFILE';
      specificCardClass = styles.unregisteredMatchCard;
      break;
    case 'registeredMatch': // This is the default .card style (red)
    default:
      labelText = 'REGISTERED USER';
      // No specific class needed, styles.card is base and handles this
      break;
  }

  // Format username to ensure it displays correctly
  let displayUsername = username;
  // Add @ prefix for registered users if not already present
  if (cardType === 'registeredMatch' && username && !username.startsWith('@') && username !== 'Registered User') {
    displayUsername = `@${username}`;
  }

  const cardClasses = `${styles.card} ${specificCardClass}`.trim();

  const [isLoading, setIsLoading] = useState(true);

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  // Default card width to ensure consistent sizing
  const defaultCardStyle = {
    width: '140px',
    marginBottom: '16px',
    ...style
  };

  return (
    <div className={cardClasses} style={defaultCardStyle}>
      {labelText && (
        <div className={styles.label}>
          {/* The span inside .label is styled by CSS based on parent card type */}
          <span>{labelText}</span>
        </div>
      )}
      <div className={styles.imageContainer}>
        <div className={styles.imageBorder}>
          <img
            src={image || 'http://localhost:5000/static/images/default_profile.svg'}
            alt={displayUsername || 'Face'}
            className={`${styles.image} ${isLoading ? styles.loading : ''}`}
            onLoad={handleImageLoad}
            onError={() => setIsLoading(false)}
          />
        </div>
      </div>
      <div className={styles.info}>
        <div className={styles.namePill}>
          <span>{displayUsername || 'Unknown'}</span>
        </div>
        <div className={styles.cityState}>
          {cardType === 'currentUser' && (
            // For currentUser, you might want to display city if available
            <span className={styles.cityStatePlaceholder}>City N/A</span>
          )}
          {(cardType === 'registeredMatch' || cardType === 'unregisteredMatch') && (state || decade) ? (
            <>
              {state && <span>{state}</span>}
              {state && decade && <span className={styles.separator}>, </span>}
              {decade && <span>{decade}</span>}
            </>
          ) : (cardType !== 'currentUser' && 
            <span className={styles.cityStatePlaceholder}>Location N/A</span>
          )}
        </div>
        {/* Show similarity only for match cards */}
        {(cardType === 'unregisteredMatch' || cardType === 'registeredMatch') && similarity !== undefined && (
          <div className={styles.similarity}>
            <span>{similarity}%</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UniversalCard;