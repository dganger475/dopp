import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    width: '40px',
    height: '40px',
    margin: '10px 0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '2px solid #030303',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#e4e6eb',
    color: '#050505',
    fontSize: '12px',
    fontFamily: 'Open Sans',
    fontWeight: 700,
    outline: 'none',
    transition: 'all 0.2s ease',
  },
  ButtonActive: {
    backgroundColor: '#1b74e4',
    borderColor: '#1b74e4',
    color: '#ffffff',
  },
  Icon: {
    fontSize: '24px',
    width: '24px',
    height: '24px',
    color: '#050505',
    fill: '#050505',
    transition: 'all 0.2s ease',
  },
  IconActive: {
    color: '#ffffff',
    fill: '#ffffff',
  }
};

const IconComponent = ({ isActive }) => (
  <svg style={{ ...styles.Icon, ...(isActive ? styles.IconActive : {}) }} viewBox="0 0 24 24">
    <path d="M24 24H0V0h24v24z" fill="none" />
    <path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.08-.66a4.8 4.8 0 0 0-.88-1.22L14 2 7.59 8.41C7.21 8.79 7 9.3 7 9.83v7.84A2.34 2.34 0 0 0 9.34 20h8.11c.7 0 1.36-.37 1.72-.97l2.66-6.15z" />
  </svg>
);

const MatchPostLikeButton = ({ isLiked = false, onClick }) => {
  return (
    <button 
      style={{ 
        ...styles.Button, 
        ...(isLiked ? styles.ButtonActive : {})
      }}
      onClick={onClick}
      aria-label={isLiked ? "Unlike" : "Like"}
    >
      <IconComponent isActive={isLiked} />
    </button>
  );
};

export default MatchPostLikeButton;