import React from 'react';

const styles = {
  Card: {
    top: '330px',
    left: '218px',
    width: '86px',
    height: '17px',
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