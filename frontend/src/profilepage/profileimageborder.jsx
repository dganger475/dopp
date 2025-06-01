import React from 'react';
import styles from './ProfileImageBorder.module.css';
import LazyImage from '../components/LazyImage';

const ProfileImageBorder = ({ image }) => {
  // Debug: Log the image prop
  console.log('ProfileImageBorder - image prop:', image);
  
  // Use the provided image or fall back to default
  const imageSrc = image || '/static/images/default_profile.svg';
  
  return (
    <div className={styles.profileImageContainer}>
      <LazyImage 
        src={imageSrc} 
        alt="Profile" 
        className={styles.image}
        onError={(e) => {
          console.error('Error loading profile image:', imageSrc);
          e.target.onerror = null; // Prevent infinite loop
          e.target.src = '/static/images/default_profile.svg';
        }}
      />
    </div>
  );
};

export default ProfileImageBorder;