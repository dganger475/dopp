import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle } from '@fortawesome/free-solid-svg-icons';

const EmptyState = () => {
  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '220px',
      gap: '15px',
      backgroundColor: 'rgba(0, 123, 255, 0.05)',
      borderRadius: '8px',
      padding: '20px',
      textAlign: 'center',
      width: '100%',
      boxSizing: 'border-box'
    }}>
      <div style={{ fontSize: '36px', color: '#007bff', opacity: '0.7' }}>
        <FontAwesomeIcon icon={faInfoCircle} />
      </div>
      <div style={{ fontWeight: 'bold', color: '#333' }}>No matches found</div>
      <div style={{ color: '#666', maxWidth: '80%' }}>Click the "Find Matches" button to discover people who look like you!</div>
    </div>
  );
};

export default EmptyState;
