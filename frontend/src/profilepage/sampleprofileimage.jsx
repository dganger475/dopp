import React from 'react';

const styles = {
  ImageContainer: {
    top: '106px',
    left: '137px',
    width: '100px',
    height: '100px',
    borderRadius: '6px',
    border: '4px solid #000000',
    boxSizing: 'border-box',
    backgroundImage: 'url(./image.png)',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: 'https://assets.api.uizard.io/api/cdn/stream/f347b34e-6dfc-4c98-af40-7a126437a37a.png',
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