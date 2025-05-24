import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './SearchResultsPage.module.css';
import NavBar from '../components/NavBar';
import UniversalCard from '../components/UniversalCard';

const SearchResultsPage = () => {
  const [userData, setUserData] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch user data
        const userResponse = await fetch('/auth/current_user', {
          credentials: 'include'
        });
        if (!userResponse.ok) throw new Error('Failed to fetch user data');
        const userData = await userResponse.json();
        setUserData(userData);

        // Fetch matches
        const matchesResponse = await fetch('/api/search', {
          credentials: 'include'
        });
        if (!matchesResponse.ok) throw new Error('Failed to fetch matches');
        const matchesData = await matchesResponse.json();
        const fetchedMatches = matchesData.results || matchesData.matches || [];
        setMatches(fetchedMatches);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handlePrevMatch = () => {
    setCurrentMatchIndex((prev) => (prev > 0 ? prev - 1 : matches.length - 1));
  };

  const handleNextMatch = () => {
    setCurrentMatchIndex((prev) => (prev < matches.length - 1 ? prev + 1 : 0));
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <div className={styles.errorMessage}>Error: {error}</div>
      </div>
    );
  }

  const currentMatch = matches[currentMatchIndex];

  return (
    <div className={styles.container}>
      <NavBar />
      <div className={styles.content}>
        {/* Main comparison section */}
        <div className={styles.comparisonSection}>
          {/* Left side - User Card */}
          <div className={styles.userCardSection}>
            <UniversalCard
              image={userData?.image || '/default_profile.png'}
              username={userData?.username || 'Your Profile'}
              label="YOU"
              labelColor="#fff"
              labelBg="#1b74e4"
              decade={userData?.decade || ''}
              state={userData?.state || ''}
              isRegistered={true}
            />
          </div>

          {/* Right side - Match Cards Carousel */}
          <div className={styles.matchCardSection}>
            {matches.length > 0 ? (
              <>
                {/* Current Match Card */}
                <UniversalCard
                  image={currentMatch.image || '/default_profile.png'}
                  username={currentMatch.username || 'Historical Match'}
                  label={currentMatch.is_registered ? 'REGISTERED' : 'HISTORICAL'}
                  labelColor="#fff"
                  labelBg={currentMatch.is_registered ? '#1b74e4' : '#000'}
                  decade={currentMatch.decade || ''}
                  state={currentMatch.state || ''}
                  similarity={currentMatch.similarity}
                  style={{ border: '2px solid #1b74e4', borderRadius: '8px' }}
                />

                {/* Navigation Buttons */}
                <div className={styles.navigationButtons}>
                  <button
                    className={styles.navButton}
                    onClick={handlePrevMatch}
                    disabled={matches.length <= 1}
                  >
                    Previous
                  </button>
                  <button
                    className={styles.navButton}
                    onClick={handleNextMatch}
                    disabled={matches.length <= 1}
                  >
                    Next
                  </button>
                </div>

                {/* Additional Matches Grid */}
                <div className={styles.additionalMatches}>
                  {matches.map((match, index) => (
                    <UniversalCard
                      key={match.id}
                      image={match.image || '/default_profile.png'}
                      username={match.username || 'Historical Match'}
                      label={match.is_registered ? 'REGISTERED' : 'HISTORICAL'}
                      labelColor="#fff"
                      labelBg={match.is_registered ? '#1b74e4' : '#000'}
                      decade={match.decade || ''}
                      state={match.state || ''}
                      similarity={match.similarity}
                      style={{
                        border: '1px solid #ddd',
                        borderRadius: '8px',
                        margin: '8px',
                        opacity: index === currentMatchIndex ? 1 : 0.7
                      }}
                    />
                  ))}
                </div>
              </>
            ) : (
              <div className={styles.noMatches}>
                No matches found
              </div>
            )}
          </div>
        </div>

        {/* Bottom carousel section */}
        <div className={styles.carouselSection}>
          <div className={styles.matchesCarousel}>
            {matches.map((match, index) => (
              <div 
                key={match.id || index}
                className={`${styles.carouselCard} ${index === currentMatchIndex ? styles.activeCard : ''}`}
                onClick={() => setCurrentMatchIndex(index)}
              >
                <UniversalCard
                  image={match.image || '/default_profile.png'}
                  username={match.username || 'Historical Match'}
                  label={match.is_registered ? 'REGISTERED' : 'HISTORICAL'}
                  labelColor="#fff"
                  labelBg={match.is_registered ? '#1b74e4' : '#000'}
                  decade={match.decade || ''}
                  state={match.state || ''}
                  similarity={match.similarity}
                  isRegistered={match.is_registered}
                  style={{ transform: 'scale(0.8)', transition: 'transform 0.2s ease' }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchResultsPage;
