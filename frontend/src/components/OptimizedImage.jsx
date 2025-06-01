import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import ErrorBoundary from './ErrorBoundary';

const OptimizedImage = ({
  src,
  alt,
  className = '',
  style = {},
  fallbackSrc,
  loading = 'lazy',
  width,
  height,
  quality = 80,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [supportsWebP, setSupportsWebP] = useState(false);

  useEffect(() => {
    // Check WebP support
    const checkWebPSupport = async () => {
      try {
        const webpImage = new Image();
        webpImage.onload = () => setSupportsWebP(true);
        webpImage.onerror = () => setSupportsWebP(false);
        webpImage.src = 'data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoBAAEAAwA0JaQAA3AA/vuUAAA=';
      } catch (e) {
        setSupportsWebP(false);
      }
    };
    checkWebPSupport();
  }, []);

  const getOptimizedSrc = (imageSrc) => {
    if (!imageSrc) return fallbackSrc;
    
    // If the image is from our API, add optimization parameters
    if (imageSrc.startsWith('/api/storage/')) {
      const params = new URLSearchParams({
        quality: quality.toString(),
        format: supportsWebP ? 'webp' : 'jpeg',
        ...(width && { width: width.toString() }),
        ...(height && { height: height.toString() })
      });
      return `${imageSrc}?${params.toString()}`;
    }
    
    return imageSrc;
  };

  const handleLoad = () => {
    setIsLoading(false);
    setError(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setError(true);
  };

  const imageStyle = {
    ...style,
    opacity: isLoading ? 0 : 1,
    transition: 'opacity 0.3s ease-in-out'
  };

  const placeholderStyle = {
    ...style,
    background: '#f0f0f0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#666',
    fontSize: '14px'
  };

  if (error && fallbackSrc) {
    return (
      <img
        src={fallbackSrc}
        alt={alt}
        className={className}
        style={imageStyle}
        loading={loading}
        {...props}
      />
    );
  }

  return (
    <ErrorBoundary
      errorMessage="Failed to load image"
      fallback={
        <div style={placeholderStyle}>
          <span>Failed to load image</span>
        </div>
      }
    >
      {isLoading && (
        <div style={placeholderStyle}>
          <span>Loading...</span>
        </div>
      )}
      <img
        src={getOptimizedSrc(src)}
        alt={alt}
        className={className}
        style={imageStyle}
        loading={loading}
        onLoad={handleLoad}
        onError={handleError}
        width={width}
        height={height}
        {...props}
      />
    </ErrorBoundary>
  );
};

OptimizedImage.propTypes = {
  src: PropTypes.string.isRequired,
  alt: PropTypes.string.isRequired,
  className: PropTypes.string,
  style: PropTypes.object,
  fallbackSrc: PropTypes.string,
  loading: PropTypes.oneOf(['lazy', 'eager']),
  width: PropTypes.number,
  height: PropTypes.number,
  quality: PropTypes.number
};

export default OptimizedImage; 