import React from 'react';

const styles = {
  ImageContainer: {
    width: '40px',
    height: '40px',
    borderRadius: '9999px',
    border: '2px solid #030303',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: '/static/images/default_profile.png',
}

const Image = (props) => {
  return (
    <div style={{
      ...styles.ImageContainer,
      backgroundImage: `url(${props.image ?? defaultProps.image})`,
    }} />
  );
};

export default Image;