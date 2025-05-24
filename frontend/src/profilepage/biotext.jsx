import React from 'react';

const styles = {
  Text: {
    color: '#ffffff',
    fontSize: '14px',
    fontFamily: 'Open Sans',
    lineHeight: '20px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'bio information written here',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;