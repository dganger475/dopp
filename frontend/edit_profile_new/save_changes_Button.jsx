import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '722px',
    left: '68px',
    width: '217px',
    height: '38px',
    padding: '0px 8px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#1b74e4',
    color: '#ffffff',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    lineHeight: '20px',
    outline: 'none',
  },
};

const defaultProps = {
  label: 'Save Changes',
};

const Button = (props) => {
  return (
    <button style={styles.Button}>
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;