import React, { useCallback } from 'react';
import ErrorBoundary from '../../components/ErrorBoundary';
import LazyImage from '../../components/LazyImage';
import styles from './matchpostavatar.module.css';

const MatchPostAvatarContent = ({ src, alt, onError }) => {
  const handleError = useCallback((error) => {
    console.error('Error in MatchPostAvatar:', error);
    if (onError) {
      onError(error);
    }
  }, [onError]);

  return (
    <div className={styles.avatarContainer}>
      <LazyImage
        src={src}
        alt={alt}
        className={styles.avatar}
        onError={handleError}
      />
    </div>
  );
};

// Wrap the component with ErrorBoundary
const MatchPostAvatar = (props) => (
  <ErrorBoundary>
    <MatchPostAvatarContent {...props} />
  </ErrorBoundary>
);

export default MatchPostAvatar;