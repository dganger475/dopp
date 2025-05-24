import React from 'react';

const styles = {
  Card: {
    width: '100%',
    maxWidth: '600px',
    backgroundColor: '#ffffff',
    borderRadius: '6px',
    border: '3px solid #030303',
    boxSizing: 'border-box',
    boxShadow: '0px 2px 26px rgba(0,0,0,0.3)',
    margin: '0 16px',
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