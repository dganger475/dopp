import React from 'react';

const styles = {
  Card: {
    top: '266px',
    left: '137px',
    width: '102px',
    height: '98px',
    backgroundColor: '#ffffff',
    borderRadius: '6.4px',
    border: '4px solid #030303',
    boxSizing: 'border-box',
    boxShadow: '0px 2px 26px rgba(0,0,0,0.3)',
  },
};

const Card = (props) => {
  return (
    <div style={styles.Card}>
      {props.children}
    </div>
  );
};

export default Card;