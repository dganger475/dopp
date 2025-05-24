// MatchCard.jsx
import React from 'react';

// --- The unified MatchCard component ---
const MatchCard = ({
  image,
  label, // "REGISTERED USER" or "UNCLAIMED PROFILE"
  username, // actual username if registered
  similarity, // "Similarity: XX%"
  stateDecade, // combined string for state/decade/location
}) => {
  const isRegistered = label === "REGISTERED USER";
  const defaultImage = 'https://via.placeholder.com/120?text=Match';
  const finalImage = image || defaultImage;

  const displayUsername = isRegistered && username ? `@${username}` : "@UNCLAIMED";

  return (
    <div 
      className={`dopple-card ${isRegistered ? 'dopple-blue-border' : 'dopple-black-border'}`}
      style={{ width: '100%', maxWidth: '320px', textAlign: 'center' }} // Centering content within the card
    >
      <div
        style={{
          backgroundColor: isRegistered ? 'var(--dopple-blue)' : '#FF8C00', // DarkOrange for unclaimed
          color: 'var(--dopple-white)',
          padding: '4px 8px',
          borderRadius: '4px',
          fontWeight: 'bold',
          fontSize: '12px',
          marginBottom: '12px',
          display: 'inline-block',
        }}
      >
        {label}
      </div>
      <img
        src={finalImage}
        alt="Match face"
        className="dopple-match-img dopple-mx-auto" // main.css class for image, mx-auto for centering if block
        style={{ width: '120px', height: '120px', marginBottom: '12px', borderRadius: '18px' }} // Ensure class styles apply
      />
      <div
        style={{
          background: isRegistered ? 'var(--dopple-blue)' : 'var(--dopple-black)',
          color: 'var(--dopple-white)',
          padding: '6px 14px',
          borderRadius: 'var(--dopple-border-radius, 16px)',
          fontWeight: '600',
          fontSize: '15px',
          marginBottom: '10px',
          display: 'inline-block',
          lineHeight: 'normal'
        }}
      >
        {displayUsername}
      </div>
      <div style={{ fontSize: '14px', color: 'var(--dopple-black)', marginBottom: '6px', fontWeight: '500' }}>
        {similarity}
      </div>
      {stateDecade && (
        <div style={{ fontSize: '13px', color: '#4A4A4A' }}>
          {stateDecade}
        </div>
      )}
    </div>
  );
};

export default MatchCard;