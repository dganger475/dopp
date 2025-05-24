import React from 'react';

const styles = {
  Card: {
    top: '298px',
    left: '52px',
    width: '100px',
    height: '24px',
    backgroundColor: '#000000',
    borderRadius: '9999px',
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