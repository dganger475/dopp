import React from 'react';

const styles = {
  Card: {
    top: '0px',
    left: '0px',
    width: '375px',
    height: '62px',
    backgroundColor: '#1b74e4',
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