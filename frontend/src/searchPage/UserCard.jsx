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
        // className="user-pill" // Not a defined class in main.css snippet, using inline with CSS vars
        style={{
          background: 'var(--dopple-black)',
          color: 'var(--dopple-white)',
          padding: '6px 14px',
          borderRadius: 'var(--dopple-border-radius, 16px)',
          fontWeight: '600',
          fontSize: '15px',
          marginBottom: '8px',
          display: 'inline-block',
          lineHeight: 'normal' // Added for better text centering in pill
        }}
      >
        {username || '@your_username'}
      </div>
      <p style={{ fontSize: '14px', color: 'var(--dopple-black)', margin: 0 }}>
        {cityState || 'Your City, ST'}
      </p>
    </div>
  );
};

export default UserCard;