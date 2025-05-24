import React from 'react';

const styles = {
  Card: {
    top: '177px',
    left: '33px',
    width: '140px',
    height: '202px',
    backgroundColor: '#1b74e4',
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