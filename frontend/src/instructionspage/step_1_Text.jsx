import React from 'react';

const styles = {
  Text: {
    color: '#4f4f4f',
    fontSize: '10px',
    fontFamily: 'Open Sans',
    lineHeight: '13px',
  },
};

const defaultProps = {
  text: 'Register and upload a selfie. Ensure your photo is clear and well-lit for the best results.',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;