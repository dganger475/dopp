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
  text: 'Click the search button and wait a minute or two for us to search the globe for your lookalikes.',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;