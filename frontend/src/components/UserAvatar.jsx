import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { getProfileImageUrl } from '../utils/imageUrls';
import { preloadImage } from '../utils/imagePreloader';
import OptimizedImage from './OptimizedImage';

/**
 * UserAvatar component for displaying user profile pictures.
 */
const UserAvatar = ({ 
  imageUrl, 
  username, 
  size = 'md', 
  shape = 'circle',
  className = '',
  style = {},
  priority = false
}) => {
  // Size presets
  const sizes = {
    sm: { width: 24, height: 24 },
    md: { width: 40, height: 40 },
    lg: { width: 64, height: 64 },
    xl: { width: 100, height: 100 }
  };

  // Shape presets
  const shapes = {
    circle: { borderRadius: '50%' },
    square: { borderRadius: '4px' }
  };

  const avatarStyle = {
    ...shapes[shape],
    overflow: 'hidden',
    ...style
  };

  // Preload avatar image if priority
  useEffect(() => {
    if (priority && imageUrl) {
      preloadImage(getProfileImageUrl(imageUrl));
    }
  }, [priority, imageUrl]);

  return (
    <div 
      className={`user-avatar ${className}`}
      style={avatarStyle}
    >
      <OptimizedImage
        src={getProfileImageUrl(imageUrl)}
        alt={username ? `${username}'s avatar` : 'User avatar'}
        width={sizes[size].width}
        height={sizes[size].height}
        quality={85}
        fallbackSrc="/static/default_profile.jpg"
        priority={priority}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover'
        }}
      />
    </div>
  );
};

UserAvatar.propTypes = {
  imageUrl: PropTypes.string,
  username: PropTypes.string,
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  shape: PropTypes.oneOf(['circle', 'square']),
  className: PropTypes.string,
  style: PropTypes.object,
  priority: PropTypes.bool
};

export default UserAvatar; 