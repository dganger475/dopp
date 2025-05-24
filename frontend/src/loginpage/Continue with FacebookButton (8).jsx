import React from 'react';

const styles = {
  Button: {
    cursor: 'pointer',
    top: '450px',
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
    backgroundColor: '#1b74e4',
    color: '#ffffff',
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
    color: '#ffffff',
    fill: '#ffffff',
  },
};

const IconComponent = () => (
  <svg></svg>
);

const defaultProps = {
  label: 'Continue with Facebook',
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