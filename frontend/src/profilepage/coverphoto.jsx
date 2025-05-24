import React from 'react';

const styles = {
  ImageContainer: {
    top: '0px',
    left: '0px',
    width: '375px',
    height: '198px',
    backgroundImage: 'url(./image.png)',
    backgroundPosition: 'center center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  },
};

const defaultProps = {
  image: 'https://assets.api.uizard.io/api/cdn/stream/f02513c6-3cae-4870-a271-896221ff91f0.png',
}

const Image = (props) => {
  return (
    <div className="coverPhoto" style={{ backgroundImage: `url(${props.image ?? defaultProps.image})` }} />
  );
};

export default Image;