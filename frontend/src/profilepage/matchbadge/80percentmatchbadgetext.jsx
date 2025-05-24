import React from 'react';
import styles from './MatchBadgeText.module.css';

const defaultProps = {
  text: '80% Match Found',
};

const Text = (props) => {
  return (
    <div className={styles.text}>
      {props.text ?? defaultProps.text}
    </div>
  );
};

export default Text;