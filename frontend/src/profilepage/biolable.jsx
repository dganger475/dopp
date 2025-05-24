import React from 'react';

const styles = {
  Text: {
    color: '#030303',
    fontSize: '8px',
    fontFamily: 'Open Sans',
    fontWeight: 600,
    lineHeight: '10px',
  },
};

const defaultProps = {
  text: 'Bio',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;