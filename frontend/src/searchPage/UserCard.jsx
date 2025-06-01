// UserCard.jsx
import React from 'react';

const UserCard = ({
  image,
  username,
  cityState,
}) => {
  const defaultImage = 'https://assets.api.uizard.io/api/cdn/stream/70fbd294-99f4-44bb-8ede-ef2ad43481d3.png';
  const finalImage = image || defaultImage;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', width: '100%' }}>
      <img
        src={finalImage}
        alt="User profile"
        className="dopple-user-img"
        style={{ 
          width: '120px', 
          height: '120px', 
          marginBottom: '12px', 
          borderRadius: '18px',
          border: '3px solid var(--dopple-black)'
        }}
      />
      <div
        style={{
          background: '#333333',
          color: '#ffffff',
          padding: '6px 14px',
          borderRadius: '8px',
          fontWeight: '600',
          fontSize: '15px',
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          width: 'auto',
          minWidth: '100px',
          maxWidth: '140px'
        }}
      >
        <span style={{
          color: '#ffffff',
          fontSize: '15px',
          fontFamily: 'Arial, sans-serif',
          fontWeight: '600',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          maxWidth: '120px',
          padding: '0 4px'
        }}>
          {username || '@your_username'}
        </span>
      </div>
      <p style={{ fontSize: '14px', color: 'var(--dopple-black)', margin: 0 }}>
        {cityState || 'Your City, ST'}
      </p>
    </div>
  );
};

export default UserCard;