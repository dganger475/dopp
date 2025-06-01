import React from 'react';
import Footer from './Footer';
import styles from './PageLayout.module.css';

const PageLayout = ({ children }) => {
  return (
    <div className={styles.layout}>
      <main className={styles.main}>
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default PageLayout; 