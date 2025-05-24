import React from 'react';

const styles = {
  Text: {
    color: '#ffffff',
    fontSize: '12px',
    fontFamily: 'Open Sans',
    fontWeight: '500',
    lineHeight: '16px',
  },
};

const defaultProps = {
  text: 'REGISTERED USER',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;