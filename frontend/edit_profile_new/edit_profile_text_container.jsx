import React from 'react';

const styles = {
  Card: {
    top: '128px',
    left: '68px',
    width: '237px',
    height: '41px',
    backgroundColor: '#1b74e4',
    borderRadius: '26px',
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