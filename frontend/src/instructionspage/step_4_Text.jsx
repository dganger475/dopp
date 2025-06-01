import React from 'react';

const styles = {
  Text: {
    color: '#4f4f4f',
    fontSize: '10px',
    fontFamily: 'Open Sans',
    lineHeight: '13px',
    textAlign: 'center',
  },
};

const defaultProps = {
  text: 'View and scroll through your lookalikes. When you see one you want to connect with, share it to your timeline or any other social platform.',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;