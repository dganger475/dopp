import React from 'react';

const styles = {
  Text: {
    color: '#030303',
    fontSize: '16px',
    fontFamily: 'Open Sans',
    fontWeight: 600,
    lineHeight: '21px',
  },
};

const defaultProps = {
  text: 'Step 1',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;