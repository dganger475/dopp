import React, { useCallback } from 'react';
import ErrorBoundary from '../../components/ErrorBoundary';
import styles from './matchpostcontainer.module.css';

const MatchPostContainerContent = ({ children, className, onError }) => {
  const handleError = useCallback((error) => {
    console.error('Error in MatchPostContainer:', error);
    if (onError) {
      onError(error);
    }
  }, [onError]);

  return (
    <div 
      className={`${styles.container} ${className || ''}`}
      onError={handleError}
    >
      {children}
    </div>
  );
};

// Wrap the component with ErrorBoundary
const MatchPostContainer = (props) => (
  <ErrorBoundary>
    <MatchPostContainerContent {...props} />
  </ErrorBoundary>
);

export default MatchPostContainer;