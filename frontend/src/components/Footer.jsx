import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.content}>
        <div className={styles.links}>
          <Link to="/about">About</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/contact">Contact</Link>
        </div>
        <div className={styles.copyright}>
          © {new Date().getFullYear()} Dopp. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer; 