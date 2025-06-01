import React from 'react';

const styles = {
  Text: {
    color: '#080a0b',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 500,
    lineHeight: '18px',
  },
};

const defaultProps = {
  text: 'Current City',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;