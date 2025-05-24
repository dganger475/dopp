import React from 'react';
import styles from './UsernamePillText.module.css';

const defaultProps = {
  text: '@username',
};

const Text = (props) => {
  return (
    <div className={styles.text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;