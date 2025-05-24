import React from 'react';

const styles = {
  Card: {
    top: '521px',
    left: '208px',
    width: '96px',
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