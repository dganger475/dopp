import React from 'react';

const styles = {
  Card: {
    top: '176px',
    left: '188px',
    width: '140px',
    height: '203px',
    backgroundColor: '#000000',
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