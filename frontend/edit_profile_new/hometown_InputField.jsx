import React from 'react';

const styles = {
  Input: {
    top: '447px',
    left: '22px',
    width: '335px',
    height: '44px',
    padding: '0px 8px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#e4e6eb',
    color: '#050505',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 500,
    lineHeight: '20px',
    outline: 'none',
  },
};

const defaultProps = {
  text: 'Enter Your Hometown',
};

const InputField = (props) => {
  return (
    <input style={styles.Input} placeholder={props.text ?? defaultProps.text} />
  );
};

export default InputField;