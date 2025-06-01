import React from 'react';

const styles = {
  Text: {
    color: '#8a8d91',
    fontSize: '14px',
    fontFamily: 'Open Sans',
    lineHeight: '20px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'Follow these steps to discover and connect with your doppelgangers around the world.',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;