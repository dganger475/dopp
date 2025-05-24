import React from 'react';

const styles = {
  Text: {
    color: '#ffffff',
    fontSize: '8px',
    fontFamily: 'Open Sans',
    lineHeight: '10px',
  },
};

const defaultProps = {
  text: 'UNCLAIMED PROFILE',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;