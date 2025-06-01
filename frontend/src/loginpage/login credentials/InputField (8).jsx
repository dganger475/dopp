import React from 'react';

const styles = {
  Input: {
    width: '100%',
    height: '44px',
    padding: '0px 12px',
    border: '1px solid #ddd',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#f5f5f5',
    color: '#333',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    fontWeight: 400,
    lineHeight: '44px',
    outline: 'none',
    transition: 'all 0.2s ease',
  },
};

const defaultProps = {
  text: 'Email',
};

const InputField = ({ value, onChange, ...props }) => {
  return (
    <input
      type="email"
      style={styles.Input}
      placeholder={props.text ?? defaultProps.text}
      value={value}
      onChange={onChange}
      required
    />
  );
};

export default InputField;