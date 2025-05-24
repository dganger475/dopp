import React from 'react';

const styles = {
  Text: {
    color: '#050505',
    fontSize: '12px',
    fontFamily: 'Source Sans Pro',
    textAlign: 'center',
    marginTop: '5px',
  },
};

const defaultProps = {
  text: 'Likes: 120',
};

const Text = (props) => {
  return (
    <div style={styles.Text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;