import React from 'react';

const styles = {
  Card: {
    top: '298px',
    left: '208px',
    width: '100px',
    height: '24px',
    backgroundColor: '#1b74e4',
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