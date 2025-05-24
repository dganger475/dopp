import React from 'react';

const styles = {
  Text: {
    color: '#ffffff',
    fontSize: '11px',
    fontFamily: 'Open Sans',
    lineHeight: '14px',
  },
};

const defaultProps = {
  text: 'CA 1990s',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;