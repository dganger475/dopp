import React from 'react';

const styles = {
  Card: {
    top: '60px',
    left: '0px',
    width: '375px',
    height: '2px',
    backgroundColor: '#000000',
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