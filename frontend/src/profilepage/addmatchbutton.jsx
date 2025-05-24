import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '298px',
    left: '8px',
    width: '125px',
    height: '27px',
    padding: '0px 8px',
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
  },
};

const defaultProps = {
  label: 'Add Match',
};

const Button = (props) => {
  return (
    <button style={styles.Button}>
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;