import React from 'react';

const styles = {
  Card: {
    top: '415px',
    left: '204px',
    width: '108px',
    height: '106px',
    backgroundColor: 'rgba(0,0,0,0)',
    borderRadius: '6px',
    border: '2.66667px solid #000000',
    boxSizing: 'border-box',
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