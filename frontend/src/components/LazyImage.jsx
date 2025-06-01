import React, { useState, useEffect } from 'react';

const LazyImage = ({ src, alt, className, style, placeholder = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7' }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(placeholder);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setCurrentSrc(src);
      setIsLoaded(true);
    };
  }, [src]);

  return (
    <img
      src={currentSrc}
      alt={alt}
      className={`${className} ${isLoaded ? 'loaded' : 'loading'}`}
      style={{
        ...style,
        transition: 'opacity 0.3s ease-in-out',
        opacity: isLoaded ? 1 : 0.5,
      }}
    />
  );
};

export default React.memo(LazyImage); 