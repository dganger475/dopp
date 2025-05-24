import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '262px',
    left: '32px',
    width: '296px',
    height: '44px',
    padding: '0px 8px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#646cff',
    color: '#fff',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    lineHeight: '20px',
    outline: 'none',
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