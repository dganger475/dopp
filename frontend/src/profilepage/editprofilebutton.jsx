import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    padding: '8px 16px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#1b74e4',
    color: '#ffffff',
    fontSize: '14px',
    fontFamily: 'Open Sans',
    fontWeight: 700,
    lineHeight: '20px',
    outline: 'none',
    transition: 'background-color 0.2s',
  },
};

const defaultProps = {
  label: 'Edit Profile',
};

const Button = ({ label = defaultProps.label, onClick }) => {
  return (
    <button 
      style={styles.Button} 
      onClick={onClick}
      onMouseOver={(e) => e.target.style.backgroundColor = '#1666ca'}
      onMouseOut={(e) => e.target.style.backgroundColor = '#1b74e4'}
    >
      {label}
    </button>
  );
};

export default Button;