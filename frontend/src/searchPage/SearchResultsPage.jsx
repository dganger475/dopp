import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import SearchResult from './SearchResult';
import styles from './SearchResultsPage.module.css';
import NavBar from '../components/NavBar';
import UniversalCard from '../components/UniversalCard';
import MatchPostCardAnimation from './MatchPostCardAnimation';
import './MatchPostCardAnimation.css';
import API_BASE_URL from '../config/api';
import MatchCard from './SearchResult';

const SearchResultsPage = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/search`, {
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch search results');
        }
        
        const data = await response.json();
        setResults(data.results || []);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching search results:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading matches...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <NavBar />
      <div className={styles.content}>
        <h1 className={styles.title}>Your Matches</h1>
        <div className={styles.resultsGrid}>
          {results.map((result, index) => (
            <SearchResult 
              key={result.id || index} 
              result={result} 
              index={index}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default SearchResultsPage;
