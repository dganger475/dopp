import React from 'react';

const styles = {
  Card: {
    top: '399px',
    left: '188px',
    width: '140px',
    height: '203px',
    backgroundColor: '#ef4444',
    borderRadius: '6px',
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