import React from 'react';

const styles = {
  Text: {
    color: '#646cff',
    fontSize: '16px',
    fontFamily: 'Source Sans Pro',
    lineHeight: '24px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'Discover your doppelgangers today',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;