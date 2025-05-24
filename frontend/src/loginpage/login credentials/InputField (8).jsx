import React from 'react';

const styles = {
  Input: {
    top: '146px',
    left: '32px',
    width: '296px',
    height: '44px',
    padding: '0px 8px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#e4e6eb',
    color: '#94a3b8',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    lineHeight: '44px',
    outline: 'none',
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