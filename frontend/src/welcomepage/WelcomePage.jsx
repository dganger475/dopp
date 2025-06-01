import React, { memo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './WelcomePage.module.css';
import ErrorBoundary from '../components/ErrorBoundary';
import LazyImage from '../components/LazyImage';
import StandardButton from '../components/StandardButton';
import PageLayout from '../components/PageLayout';
import Footer from '../components/Footer';

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

const WelcomePageContent = () => {
  const navigate = useNavigate();

  const handleLoginClick = useCallback(() => {
    navigate('/login');
  }, [navigate]);

  return (
    <PageLayout>
      <div className={styles.welcomePage}>
        <div className={styles.welcomeContent}>
          <Logo />
          <h1 className={styles.welcomeHeading}>Welcome to DoppleGänger</h1>
          <p className={styles.welcomeTagline}>
            Find your historical doppelgänger, connect, and explore!
          </p>
          <StandardButton 
            onClick={handleLoginClick}
            className={styles.welcomeButton}
            variant="primary"
            size="large"
          >
            Get Started
          </StandardButton>
        </div>
        <Footer />
      </div>
    </PageLayout>
  );
};

// Wrap the component with ErrorBoundary
const WelcomePage = () => (
  <ErrorBoundary>
    <WelcomePageContent />
  </ErrorBoundary>
);

export default WelcomePage;
