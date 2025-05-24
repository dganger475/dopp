import React from 'react';

const styles = {
  Text: {
    color: '#050505',
    fontSize: '20px',
    fontFamily: 'Open Sans',
    fontWeight: 700,
    lineHeight: '28px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'User\'s Full Name',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;