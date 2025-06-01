import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    width: '100%',
    height: '44px',
    padding: '0px 16px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#646cff',
    color: '#fff',
    fontSize: '16px',
    fontFamily: 'Arial, sans-serif',
    fontWeight: 700,
    lineHeight: '44px',
    outline: 'none',
    transition: 'background-color 0.2s ease',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
};

const defaultProps = {
  label: 'Log In',
};

const Button = ({ onClick, type = 'submit', ...props }) => {
  return (
    <button
      style={styles.Button}
      onClick={onClick}
      type={type}
    >
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;