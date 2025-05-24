import React from 'react';

const styles = {
  Input: {
    top: '251px',
    left: '5px',
    width: '149px',
    height: '36px',
    padding: '0px 8px',
    border: '3px solid #505050',
    boxSizing: 'border-box',
    borderRadius: '6px',
    boxShadow: '0px 2px 8px rgba(0,0,0,0.16)',
    backgroundColor: '#ffffff',
    color: '#000000',
    fontSize: '14px',
    fontFamily: 'Roboto',
    lineHeight: '24px',
    outline: 'none',
  },
};

const defaultProps = {
  text: 'Input Field',
};

const InputField = (props) => {
  return (
    <input style={styles.Input} placeholder={props.text ?? defaultProps.text} />
  );
};

export default InputField;