import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSyncAlt } from '@fortawesome/free-solid-svg-icons';

const LoadingState = () => {
  return (
    <div style={{ 
      textAlign: 'center', 
      width: '100%', 
      fontFamily: 'var(--dopple-font)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '220px',
      gap: '15px'
    }}>
      <div className="loading-cards">
        <div className="card-placeholder" style={{
          width: '140px',
          height: '240px',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderRadius: '6px',
          position: 'relative',
          margin: '0 5px',
          animation: 'pulse 1.5s infinite'
        }}></div>
        <div className="card-placeholder" style={{
          width: '140px',
          height: '240px',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderRadius: '6px',
          position: 'relative',
          margin: '0 5px',
          animation: 'pulse 1.5s infinite',
          animationDelay: '0.3s'
        }}></div>
        <div className="card-placeholder" style={{
          width: '140px',
          height: '240px',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderRadius: '6px',
          position: 'relative',
          margin: '0 5px',
          animation: 'pulse 1.5s infinite',
          animationDelay: '0.6s'
        }}></div>
      </div>
      <style>
        {`
          @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 0.8; }
            100% { opacity: 0.6; }
          }
          .loading-cards {
            display: flex;
            gap: 15px;
          }
        `}
      </style>
      <div style={{ fontWeight: 'bold', color: '#007bff' }}>
        <FontAwesomeIcon icon={faSyncAlt} spin /> Finding your best matches...
      </div>
    </div>
  );
};

export default LoadingState;
