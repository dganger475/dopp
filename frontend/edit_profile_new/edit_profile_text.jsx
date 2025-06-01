import React from 'react';

const styles = {
  Text: {
    color: '#080a0b',
    fontSize: '32px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    lineHeight: '40px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'Edit Your Profile ',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;