import React from 'react';

const styles = {
  Text: {
    color: '#646cff',
    fontSize: '24px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 300,
    lineHeight: '32px',
  },
};

const defaultProps = {
  text: 'Create New Account',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;