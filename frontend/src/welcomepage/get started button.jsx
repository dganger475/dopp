import React from 'react';

const styles = {
  button: {
    backgroundColor: '#646cff',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '18px',
    fontWeight: 700,
    cursor: 'pointer',
    margin: '20px 0',
    transition: 'background 0.2s',
  },
};

const defaultProps = {
  label: 'Get Started',
};

const Button = (props) => {
  return (
    <button style={styles.button}>
      {props.label ?? defaultProps.label}
    </button>
  );
};

export default Button;