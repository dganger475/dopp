import React from 'react';

const styles = {
  ImageContainer: {
    top: '0px',
    left: '0px',
    width: '375px',
    height: '316px',
    backgroundImage: 'url(./image.png)',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: 'https://assets.api.uizard.io/api/cdn/stream/5cd21e40-8bd0-4ff6-be4e-c95407982ae5.png',
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