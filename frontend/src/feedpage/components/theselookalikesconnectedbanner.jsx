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
    borderRadius: '6px 6px 0 0',
    backgroundColor: '#1b74e4',
    color: '#ffffff',
    fontSize: '14px',
    fontFamily: 'Open Sans',
    fontWeight: 700,
    outline: 'none',
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