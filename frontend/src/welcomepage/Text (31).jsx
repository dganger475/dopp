import React from 'react';

const styles = {
  Text: {
    color: '#646cff',
    fontSize: '32px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 800,
    lineHeight: '42px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'Find and Connect with People that look like you',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;