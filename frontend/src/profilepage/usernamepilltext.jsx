import React from 'react';
import styles from './UsernamePillText.module.css';

const defaultProps = {
  text: '@username',
};

const Text = (props) => {
  return (
    <div className={styles.text} style={props.style}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;