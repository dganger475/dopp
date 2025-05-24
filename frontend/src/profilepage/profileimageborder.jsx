import React from 'react';
import styles from './ProfileImageBorder.module.css';

const defaultProps = {
  image: '/static/images/default_profile.svg',
};

const ProfileImageBorder = ({ image = defaultProps.image }) => {
  return (
    <div className={styles.imageContainer}>
      <img src={image} alt="Profile" className={styles.image} />
    </div>
  );
};

export default ProfileImageBorder;