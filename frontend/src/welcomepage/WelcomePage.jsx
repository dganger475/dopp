import React, { memo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './WelcomePage.module.css';
import ErrorBoundary from '../components/ErrorBoundary';
import LazyImage from '../components/LazyImage';

// Memoized logo component
const Logo = memo(() => (
  <LazyImage
    src="/static/images/logo.png"
    alt="DoppleGänger Logo"
    className={styles.welcomeLogo}
    onError={(e) => {
      console.warn('Failed to load logo:', e);
      e.target.src = '/static/images/default_logo.png';
    }}
  />
));

// Memoized button component
const LoginButton = memo(({ onClick }) => (
  <button onClick={onClick} className={styles.welcomeButton}>
    Login / Register
  </button>
));

const WelcomePageContent = () => {
  const navigate = useNavigate();

  const handleLoginClick = useCallback(() => {
    navigate('/login');
  }, [navigate]);

  return (
    <div className={styles.welcomePage}>
      <Logo />
      <h1 className={styles.welcomeHeading}>Welcome to DoppleGänger</h1>
      <p className={styles.welcomeTagline}>
        Find your historical doppelgänger, connect, and explore!
      </p>
      <LoginButton onClick={handleLoginClick} />
    </div>
  );
};

// Wrap the component with ErrorBoundary
const WelcomePage = () => (
  <ErrorBoundary>
    <WelcomePageContent />
  </ErrorBoundary>
);

export default WelcomePage;
