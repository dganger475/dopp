import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faShare, faPlus, faArrowLeft } from '@fortawesome/free-solid-svg-icons';
import NavBar from '../components/NavBar';
import API_BASE_URL, { getApiUrl } from '../config/api';
import styles from './ComparisonPage.module.css';
import { useSharedMatch } from '../context/SharedMatchContext';
import StandardButton from '../components/StandardButton';
import MatchPostCardAnimation from './MatchPostCardAnimation';
import './MatchPostCardAnimation.css';
import SearchResult from '../searchPage/SearchResult';
import ErrorBoundary from '../components/ErrorBoundary';
import LazyImage from '../components/LazyImage';

const ComparisonPageContent = () => {
  const navigate = useNavigate();
  const { matchId } = useParams();
  const location = useLocation();
  const { shareMatch } = useSharedMatch();
  
  // State for user and match data
  const [userData, setUserData] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [shareAnimation, setShareAnimation] = useState(false);
  const [isShared, setIsShared] = useState(false);
  
  // Get data from location state or fetch from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to get data from location state first
        if (location.state && location.state.matchData) {
          // We have match data from state, just need user data
          const userResponse = await fetch(getApiUrl('/api/current_user'), {
            credentials: 'include',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          });
          
          if (!userResponse.ok) {
            throw new Error('Failed to fetch user data');
          }
          
          const userData = await userResponse.json();
          setUserData(userData);
          setMatchData(location.state.matchData);
          setLoading(false);
          return;
        }
        
        // If we don't have state data, we need to redirect back to search
        // as we don't have a proper API endpoint to fetch individual match data
        console.error('No match data provided in state');
        setError('Match data not found. Please return to search and try again.');
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
        setLoading(false);
      }
    };
    
    fetchData();
  }, [matchId, location.state]);
  
  // Handle share button click - share match to feed
  const handleShare = async () => {
    try {
      // Set animation and shared states
      setShareAnimation(true);
      setIsShared(true);
      
      // Wait for animation to start before making API call
      setTimeout(async () => {
        try {
          // Extract the face filename from the match image URL
          let extractedFilename = null;
          try {
            // First try to get filename from matchData
            if (matchData?.filename && typeof matchData.filename === 'string' && matchData.filename.trim() !== '') {
              extractedFilename = matchData.filename.trim().replace(/^\/+|\/+$/g, '');
            } else if (matchData?.image && typeof matchData.image === 'string') {
              // If no filename, try to extract from image URL
              let imageUrl = matchData.image.trim();
              if (imageUrl.includes('/static/faces/')) {
                extractedFilename = imageUrl.split('/static/faces/').pop();
              } else if (imageUrl.includes('/static/extracted_faces/')) {
                extractedFilename = imageUrl.split('/static/extracted_faces/').pop();
              } else if (imageUrl.includes('/')) {
                extractedFilename = imageUrl.split('/').pop();
              } else {
                extractedFilename = imageUrl;
              }
              if (extractedFilename) extractedFilename = extractedFilename.replace(/^\/+|\/+$/g, '');
            }
            if (!extractedFilename) {
              console.error('No valid match image filename found. Using fallback.');
              extractedFilename = 'default_match.png'; // fallback image
            }
          } catch (filenameError) {
            console.error('Error extracting match image filename:', filenameError);
            extractedFilename = 'default_match.png';
          }
          
          console.log('Extracted filename:', extractedFilename);
          
          // Prepare post data
          const postData = {
            content: `I found my historical doppelganger with ${similarityPercentage}% similarity!`,
            face_filename: extractedFilename,
            is_match_post: true
          };
          
          // Make API call to save match to feed
          try {
            console.log('Sending post data to API:', postData);
            const response = await fetch(`${API_BASE_URL}/api/social/feed/create_post`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              credentials: 'include',
              body: JSON.stringify(postData)
            });
            
            if (!response.ok) {
              console.warn(`API call to save match to feed failed with status: ${response.status}`);
              try {
                const errorData = await response.json();
                console.error('Error details:', errorData);
              } catch (jsonError) {
                console.error('Could not parse error response as JSON');
              }
            } else {
              console.log('Post created successfully');
              const responseData = await response.json();
              console.log('Response data:', responseData);
            }
          } catch (apiError) {
            console.warn('API error when saving match to feed, but using client-side data:', apiError);
          }
          
          // Navigate to feed after animation completes
          setTimeout(() => {
            navigate('/social/feed');
          }, 1000);
        } catch (error) {
          console.error('Error sharing match:', error);
          setError('Failed to share match');
          setShareAnimation(false);
          setIsShared(false);
        }
      }, 1500);
    } catch (error) {
      console.error('Error in share handler:', error);
      setShareAnimation(false);
      setIsShared(false);
    }
  };
  
  // Handle add button click - add match to profile
  const handleAddToProfile = async () => {
    try {
      // In a real implementation, you would make an API call here
      // await fetch(getApiUrl('/api/add-match'), {
      //   method: 'POST',
      //   credentials: 'include',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({
      //     matchId: matchData.id
      //   })
      // });
      
      // Navigate back to profile
      navigate('/profile');
    } catch (error) {
      console.error('Error adding match to profile:', error);
      setError('Failed to add match to profile');
    }
  };
  
  // Handle back button click
  const handleBack = () => {
    navigate(-1);
  };
  
  // Helper to build a user card in unified format
  const buildUserCard = (user) => {
    if (!user) return null;
    return {
      id: user.id,
      image: user.profile_image_url || '/static/images/default_profile.svg',
      username: user.username || 'You',
      label: 'YOU',
      similarity: null,
      stateDecade: user.detail || '',
      is_registered: true
    };
  };
  
  // Helper to build a match card in unified format
  const buildMatchCard = (match) => {
    if (!match) return null;
    // Try to use the unified card structure if present
    if (match.image && match.label) return match;
    // Otherwise, normalize
    return {
      id: match.id,
      image: match.image || match.filename || '/static/images/default_profile.svg',
      username: match.username || match.id || 'Match',
      label: 'UNCLAIMED PROFILE',
      similarity: match.similarity || null,
      stateDecade: match.stateDecade || '',
      is_registered: false
    };
  };
  
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}></div>
        <p>Loading comparison...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={handleBack} className={styles.backButton}>
          <FontAwesomeIcon icon={faArrowLeft} /> Go Back
        </button>
      </div>
    );
  }
  
  // Unified card data for user and match
  const userCard = buildUserCard(userData?.user);
  const matchCard = buildMatchCard(matchData);
  
  // Prepare image URLs - never use default images for face matching
  const userImageUrl = userData?.user?.profile_image_url || null;
  const matchImageUrl = matchData?.image || matchData?.filename ? 
    (matchData.image?.startsWith('http') || matchData.filename?.startsWith('http') ? 
      (matchData.image || matchData.filename) : 
      `${API_BASE_URL}${matchData.image || matchData.filename}`) : 
    null;
  
  // Get match similarity percentage - ensure it's accurate and matches the search screen
  const similarityPercentage = matchData?.similarity ? 
    (typeof matchData.similarity === 'number' ? 
      // If it's already a number, check if it's a decimal or whole number
      (matchData.similarity <= 1 ? Math.round(matchData.similarity * 100) : Math.round(matchData.similarity)) : 
      // If it's a string, parse it and check if it needs to be multiplied
      (parseFloat(matchData.similarity) <= 1 ? Math.round(parseFloat(matchData.similarity) * 100) : Math.round(parseFloat(matchData.similarity)))) : 
    0;
  
  return (
    <div className={styles.comparisonPageContainer}>
      <NavBar />
      <div className={styles.comparisonContent}>
        <button className={styles.backButton} onClick={handleBack}>
          <FontAwesomeIcon icon={faArrowLeft} /> Back
        </button>
        <div className={styles.cardsRow}>
          {/* User Card */}
          {userCard && (
            <SearchResult result={userCard} index={0} hideSimilarity={true} />
          )}
          {/* Match Card */}
          {matchCard ? (
            <SearchResult result={matchCard} index={1} />
          ) : (
            // fallback: old rendering
            <div className={styles.matchCardFallback}>
              <img src={matchData?.image || '/static/images/default_profile.svg'} alt="Match" />
              <div>{matchData?.username || matchData?.id || 'Match'}</div>
            </div>
          )}
        </div>
        {/* Extra data and actions below cards */}
        <div className={styles.actionsContainer}>
          <StandardButton 
            text="Share to Feed"
            onClick={handleShare}
            disabled={isShared}
            type="primary"
            icon={<FontAwesomeIcon icon={faShare} />}
            style={{
              width: '100%',
              maxWidth: '300px',
              margin: '0 auto',
              border: 'none',
              boxShadow: 'rgba(0, 0, 0, 0.4) 0px 12px 32px, rgba(0, 0, 0, 0.3) 0px 6px 16px, rgba(0, 0, 0, 0.2) 0px 3px 8px',
              transition: 'all 0.2s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 'rgba(0, 0, 0, 0.5) 0px 16px 40px, rgba(0, 0, 0, 0.4) 0px 8px 20px, rgba(0, 0, 0, 0.3) 0px 4px 10px'
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};

// Wrap the component with ErrorBoundary
const ComparisonPage = () => (
  <ErrorBoundary>
    <ComparisonPageContent />
  </ErrorBoundary>
);

export default ComparisonPage;
