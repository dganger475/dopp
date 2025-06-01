import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    width: '100%',
    height: '30px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    boxSizing: 'border-box',
    borderRadius: '8px',
    backgroundColor: '#1b74e4',
    color: '#ffffff',
    fontSize: '14px',
    fontFamily: 'Open Sans',
    fontWeight: 700,
    outline: 'none',
    boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px',
    transition: 'all 0.2s ease',
    '&:hover': {
      boxShadow: 'rgba(0, 0, 0, 0.4) 0px 12px 24px, rgba(0, 0, 0, 0.3) 0px 6px 12px',
      transform: 'translateY(-1px)'
    }
  },
};

const defaultProps = {
  label: 'These Lookalikes have Connected!',
};

const Button = (props) => {
  return (
    <button style={styles.Button}>
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;