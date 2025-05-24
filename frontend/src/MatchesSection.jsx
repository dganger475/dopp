import React, { useState, useEffect } from 'react';
import API_BASE_URL from "./config/api"; 
import UniversalCard from './components/UniversalCard';
// import styles from './MatchesSection.module.css'; // Optional: for component-specific styles

const MatchesSection = ({ userId, isCurrentUser }) => {
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [matchesError, setMatchesError] = useState(null);

  useEffect(() => {
    if (!userId) {
      setLoadingMatches(false);
      setMatchesError("User ID is not provided.");
      return;
    }

    const fetchUserMatches = async () => {
      setLoadingMatches(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/matches`, {
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch matches (status: ${response.status})`);
        }
        const data = await response.json();
        
        const formattedMatches = (data.matches || data || []).map(match => ({
          id: match.id,
          image: match.image_url || match.match_image_url || (match.filename ? `${API_BASE_URL}/face/image/${match.id}` : '/static/default_profile.png'),
          username: match.name || match.match_name || 'Match',
          label: match.type || (match.relationship === 'UNCLAIMED PROFILE' ? 'Unclaimed' : 'Match'),
          labelColor: '#fff',
          labelBg: match.type === 'claimed' ? 'var(--dopple-blue)' : (match.relationship === 'UNCLAIMED PROFILE' ? 'var(--dopple-black)' : 'var(--dopple-green)'),
          decade: match.decade || '',
          state: match.state || '',
          similarity: match.similarity !== undefined ? (match.similarity > 1 ? Math.round(match.similarity) : Math.round(match.similarity * 100)) : undefined,
          isRegistered: match.relationship !== 'UNCLAIMED PROFILE',
        }));
        setMatches(formattedMatches);
      } catch (err) {
        setMatchesError(err.message);
      } finally {
        setLoadingMatches(false);
      }
    };

    fetchUserMatches();
  }, [userId]);

  if (loadingMatches) {
    return <div className="loading-placeholder" style={{textAlign: 'center', padding: '20px'}}>Loading matches...</div>;
  }

  if (matchesError) {
    return <div className="error-placeholder" style={{textAlign: 'center', padding: '20px', color: 'red'}}>Error loading matches: {matchesError}</div>;
  }

  if (matches.length === 0) {
    return <div className="empty-placeholder" style={{textAlign: 'center', padding: '20px'}}>No matches found for this user.</div>;
  }

  return (
    <div /*className={styles.matchesGrid}*/ style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'center' }}>
      {matches.map((match) => (
        <UniversalCard
          key={match.id}
          image={match.image}
          username={match.username}
          label={match.label}
          labelColor={match.labelColor}
          labelBg={match.labelBg}
          decade={match.decade}
          state={match.state}
          similarity={match.similarity}
          isRegistered={match.isRegistered}
        />
      ))}
    </div>
  );
};

export default MatchesSection;
