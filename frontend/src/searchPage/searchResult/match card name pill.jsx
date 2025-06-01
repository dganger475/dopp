import React from 'react';

const styles = {
  Card: {
    top: '298px',
    left: '208px',
    width: '150px',  // 1.5x wider
    height: '36px',  // 1.5x taller
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