import React from 'react';

const styles = {
  ImageContainer: {
    top: '35px',
    left: '99px',
    width: '179px',
    height: '114px',
    borderRadius: '8px',
    backgroundImage: 'url(./image.png)',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: 'https://assets.api.uizard.io/api/cdn/stream/dfbff6fd-c9d2-4088-ae33-77cc19e203eb.png',
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