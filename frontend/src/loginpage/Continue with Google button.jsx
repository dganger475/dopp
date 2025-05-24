import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '506px',
    left: '32px',
    width: '296px',
    height: '44px',
    padding: '0px 8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row-reverse',
    gap: '7px',
    border: '0',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#e4e6eb',
    color: '#050505',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    lineHeight: '20px',
    outline: 'none',
  },
  Icon: {
    fontSize: '21px',
    width: '21px',
    height: '21px',
    color: '#050505',
    fill: '#050505',
  },
};

const IconComponent = () => (
  <svg></svg>
);

const defaultProps = {
  label: 'Continue with Google',
  IconComponent,
};

const Button = (props) => {
  return (
    <button style={styles.Button}>
      <span>{props.label ?? defaultProps.label}</span>
      {
        props.IconComponent 
          ? <props.IconComponent style={styles.Icon} /> 
          : <defaultProps.IconComponent />
      }
    </button>
  );
};

export default Button;