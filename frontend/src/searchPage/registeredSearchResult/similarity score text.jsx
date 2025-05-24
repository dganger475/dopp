import React from 'react';

const styles = {
  Text: {
    color: '#000000',
    fontSize: '12px',
    fontFamily: 'Open Sans',
    lineHeight: '16px',
  },
};

const defaultProps = {
  text: 'Similarity: 78%',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;