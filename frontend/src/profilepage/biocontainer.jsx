import React from 'react';

const styles = {
  Card: {
    top: '256px',
    left: '77px',
    width: '228px',
    height: '36px',
    backgroundColor: '#030303',
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