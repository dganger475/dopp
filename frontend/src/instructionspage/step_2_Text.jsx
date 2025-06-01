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
  text: 'Click the looking glass icon on the blue nav bar across the top of the screen.',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;