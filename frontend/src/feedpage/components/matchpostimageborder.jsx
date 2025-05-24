import React from 'react';

const styles = {
  ImageContainer: {
    width: '100%',
    maxWidth: '400px',
    aspectRatio: '1',
    borderRadius: '6px',
    border: '4px solid #030303',
    boxSizing: 'border-box',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: 'https://assets.api.uizard.io/api/cdn/stream/61c6c67a-dd4d-46a1-9506-cf6b78c44070.png',
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