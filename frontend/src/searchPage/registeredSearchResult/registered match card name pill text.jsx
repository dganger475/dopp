import React from 'react';

const styles = {
  Text: {
    color: '#ffffff',
    fontSize: '12px',
    fontFamily: 'Open Sans',
    lineHeight: '16px',
  },
};

const defaultProps = {
  text: '@match2',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;