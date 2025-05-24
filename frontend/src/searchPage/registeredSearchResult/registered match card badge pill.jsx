import React from 'react';

const styles = {
  Card: {
    top: '399px',
    left: '193px',
    width: '130px',
    height: '26px',
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