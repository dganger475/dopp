import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '629px',
    left: '101px',
    width: '182px',
    height: '56px',
    padding: '0px 8px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#1b74e4',
    color: '#000000',
    fontSize: '16px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 500,
    lineHeight: '21px',
    outline: 'none',
  },
};

const defaultProps = {
  label: 'Continue',
};

const Button = (props) => {
  return (
    <button style={styles.Button}>
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;