import React from 'react';

const styles = {
  Card: {
    top: '554px',
    left: '209px',
    width: '87px',
    height: '16px',
    backgroundColor: '#ffffff',
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