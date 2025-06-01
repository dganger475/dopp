import React, { useState, useEffect, useCallback, useMemo } from 'react';
import API_BASE_URL, { getApiUrl } from "./config/api";
import { useNavigate } from 'react-router-dom';
import styles from './ProfilePage.module.css';
import './ProfilePageOverrides.css'; // Import direct CSS overrides
import ProfileImageBorder from './profilepage/profileimageborder';
// Import the match card name pill components instead
import NamePill from './searchPage/searchResult/match card name pill';
import NamePillText from './searchPage/searchResult/match card name pill text';
import BioContainer from './profilepage/biocontainer';
import EditProfileButton from './profilepage/editprofilebutton';
import AddMatchButton from './profilepage/addmatchbutton';
import UniversalCard from './components/UniversalCard';
import ErrorBoundary from './components/ErrorBoundary';
import LazyImage from './components/LazyImage';

const MOBILE_BREAKPOINT = 768;
const CACHE_EXPIRATION = 24 * 60 * 60 * 1000; // 24 hours

// Memoized loading component
const LoadingSpinner = React.memo(() => (
  <div className={styles.loadingContainer}>
    <div className={styles.loadingSpinner}></div>
    <p>Loading profile...</p>
  </div>
));

// Memoized error component
const ErrorDisplay = React.memo(({ error, onRetry }) => (
  <div className={styles.errorContainer}>
    <h2>Error Loading Profile</h2>
    <p>{error}</p>
    <button onClick={onRetry} className={styles.retryButton}>
      Retry
    </button>
  </div>
));

const ProfilePageContent = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [matchesError, setMatchesError] = useState(null);
  const navigate = useNavigate();
  const [imageLoading, setImageLoading] = useState({
    profile: true,
    cover: true
  });

  // Memoized handlers
  const handleRetry = useCallback(() => {
    window.location.reload();
  }, []);

  const handleImageLoad = useCallback((type) => {
    setImageLoading(prev => ({ ...prev, [type]: false }));
    const imageUrl = type === 'profile' ? getProfileImageUrl() : getCoverPhotoUrl();
    const cacheKey = `cached_${type}_image`;
    const cacheData = {
      url: imageUrl,
      timestamp: Date.now()
    };
    try {
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (err) {
      console.warn('Failed to cache image:', err);
    }
  }, []);

  const handleImageError = useCallback((type) => {
    setImageLoading(prev => ({ ...prev, [type]: false }));
    const cacheKey = `cached_${type}_image`;
    try {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        const { url, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < CACHE_EXPIRATION) {
          return url;
        }
      }
    } catch (err) {
      console.warn('Failed to read cached image:', err);
    }
    return type === 'profile' ? getApiUrl('/static/images/default_profile.svg') : getApiUrl('/static/images/default_cover_photo.png');
  }, []);

  // Memoized URL getters
  const getProfileImageUrl = useCallback(() => {
    if (!userProfile?.user) return getApiUrl('/static/images/default_profile.svg');
    
    const userData = userProfile.user;
    let imageUrl = userData.profile_image_url || userData.profile_picture;
    
    if (!imageUrl) return getApiUrl('/static/images/default_profile.svg');
    
    // Ensure the URL is absolute
    if (!imageUrl.startsWith('http')) {
      imageUrl = getApiUrl(imageUrl);
    }
    
    // Add cache-busting only if we have an update timestamp
    const lastUpdate = userData.profile_image_updated_at || userData.updated_at;
    if (lastUpdate) {
      const timestamp = new Date(lastUpdate).getTime();
      return `${imageUrl}${imageUrl.includes('?') ? '&' : '?'}t=${timestamp}`;
    }
    
    return imageUrl;
  }, [userProfile]);

  const getCoverPhotoUrl = useCallback(() => {
    if (!userProfile?.user) return getApiUrl('/static/images/default_cover_photo.png');
    
    const userData = userProfile.user;
    let imageUrl = userData.cover_photo_url || userData.cover_photo;
    
    if (!imageUrl) return getApiUrl('/static/images/default_cover_photo.png');
    
    // Ensure the URL is absolute
    if (!imageUrl.startsWith('http')) {
      imageUrl = getApiUrl(imageUrl);
    }
    
    // Add cache-busting only if we have an update timestamp
    const lastUpdate = userData.cover_photo_updated_at || userData.updated_at;
    if (lastUpdate) {
      const timestamp = new Date(lastUpdate).getTime();
      return `${imageUrl}${imageUrl.includes('?') ? '&' : '?'}t=${timestamp}`;
    }
    
    return imageUrl;
  }, [userProfile]);

  // Memoized user data
  const userData = useMemo(() => userProfile?.user || null, [userProfile]);
  const memberSince = useMemo(() => {
    if (!userData) return 'Unknown';
    const date = userData.memberSince || userData.created_at;
    return date ? new Date(date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'Unknown';
  }, [userData]);

  const currentCity = useMemo(() => 
    userData?.current_city || userData?.current_location_city || 'Location Unknown',
    [userData]
  );

  // Remove existing styles from wrong server
  useEffect(() => {
    const removeWrongServerStyles = () => {
      const links = document.querySelectorAll('link[rel="stylesheet"][href]');
      links.forEach(link => {
        if (link.href.includes(':5173')) {
          link.remove();
        }
      });
    };
    removeWrongServerStyles();
  }, []);

  // Handle responsive layout
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Add a state to track if we need to force refresh
  const [forceRefresh, setForceRefresh] = useState(0);
  
  // Force a refresh when component mounts or when returning from edit page
  useEffect(() => {
    // Increment the force refresh counter to trigger a data reload
    const timer = setTimeout(() => {
      setForceRefresh(prev => prev + 1);
    }, 100); // Small delay to ensure component is fully mounted
    
    return () => clearTimeout(timer);
  }, []);
  
  // Fetch user data
  useEffect(() => {
    // Force refresh when returning from edit profile page or when forceRefresh changes
    const fetchUserData = async () => {
      // Clear any cached data
      setUserProfile(null);
      localStorage.removeItem('profileData'); // Clear any localStorage cache
      
      try {
        // Add cache-busting parameter to prevent browser caching
        const timestamp = new Date().getTime();
        const url = `${API_BASE_URL}/api/profile/data`;
        console.log('Fetching fresh profile data from:', url);
        
        const response = await fetch(url, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
          },
          cache: 'no-store' // Tell fetch to bypass the HTTP cache
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to fetch user data: ${response.status} ${response.statusText}`);
        }
        
        // Check if we got HTML instead of JSON (this sometimes happens)
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('text/html')) {
          const html = await response.text();
          console.error('Received HTML instead of JSON:', html.substring(0, 500));
          throw new Error('Received HTML instead of JSON. Please refresh the page.');
        }
        
        const data = await response.json();
        console.log('Received profile data:', data);
        
        if (!data.success) {
          throw new Error(data.message || 'Failed to fetch user data');
        }
        
        // Process the user profile data which includes matches
        processUserProfile(data);
      } catch (err) {
        console.error('Error in fetchUserData:', err);
        setError(err.message);
        // Show a more user-friendly error message
        setError(`Unable to load profile data. ${err.message}. Please try refreshing the page.`);
      } finally {
        setLoading(false);
      }
    };

    // The matches are included in the profile data
    const processUserProfile = (data) => {
      setUserProfile(data);
      if (data && data.matches) {
        setMatches(data.matches);
        setLoadingMatches(false);
      }
    };
    
    const fetchMatches = async () => {
      // This is now just a fallback in case the profile data doesn't include matches
      try {
        if (userProfile && userProfile.matches) {
          setMatches(userProfile.matches);
          setLoadingMatches(false);
          return;
        }
        
        // Use the correct endpoint for fetching matches
        const matchesResponse = await fetch(`${API_BASE_URL}/social/matches/api/matches/sync`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        if (!matchesResponse.ok) {
          throw new Error('Failed to fetch matches');
        }
        const data = await matchesResponse.json();
        setMatches(data.matches || []);
      } catch (err) {
        console.error('Error fetching matches:', err);
        setMatchesError(err.message);
      } finally {
        setLoadingMatches(false);
      }
    };

    fetchUserData();
    fetchMatches();
    
    // Add a listener for when the page becomes visible again
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Page is now visible, refreshing profile data');
        fetchUserData();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [forceRefresh]);  // Include forceRefresh to ensure data is refreshed when it changes

  // Ensure we're properly mounted at the expected route
  useEffect(() => {
    document.title = 'Profile | DoppleGanger';
  }, []);

  return (
    <div className={styles.profileContainer}>
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorDisplay error={error} onRetry={handleRetry} />
      ) : !userProfile?.user ? (
        <ErrorDisplay 
          error="Unable to load profile data. Please try refreshing the page." 
          onRetry={handleRetry} 
        />
      ) : (
        <>
          {/* Cover Photo */}
          <div className={`${styles.coverPhotoContainer} ${imageLoading.cover ? styles.imageLoading : ''}`}>
            <LazyImage
              src={getCoverPhotoUrl()}
              alt="Cover photo"
              className={`${styles.coverPhoto} ${styles.progressiveImage} ${!imageLoading.cover ? styles.loaded : ''}`}
              onLoad={() => handleImageLoad('cover')}
              onError={(e) => {
                console.warn('Failed to load cover photo:', e.target.src);
                e.target.src = getApiUrl('/static/images/default_cover_photo.png');
                handleImageError('cover');
              }}
            />
            {imageLoading.cover && (
              <div className={styles.loadingPlaceholder}>
                Loading cover photo...
              </div>
            )}
            
            <AddMatchButton profile={userData} className={styles.addMatchBtn} />
            <EditProfileButton onClick={() => navigate('/edit-profile')} className={styles.editProfileBtn} />
          </div>

          {/* Profile Header */}
          <div className={styles.profileHeader}>
            <div className={styles.memberSinceSide}>
              <div className={styles.memberSinceLabel}>Member since</div>
              <div className={styles.memberSinceDate}>{memberSince}</div>
            </div>
            
            <div className={styles.locationContainer}>
              {currentCity}
            </div>
            
            <div className={styles.profileImageWrapper}>
              <div className={`${styles.profileImageContainer} ${imageLoading.profile ? styles.imageLoading : ''}`}>
                <ProfileImageBorder
                  image={getProfileImageUrl()}
                  onLoad={() => handleImageLoad('profile')}
                  onError={(e) => {
                    console.warn('Failed to load profile photo:', e.target.src);
                    e.target.src = getApiUrl('/static/images/default_profile.svg');
                    handleImageError('profile');
                  }}
                  className={`${styles.progressiveImage} ${!imageLoading.profile ? styles.loaded : ''}`}
                />
                {imageLoading.profile && (
                  <div className={styles.loadingPlaceholder}>
                    Loading profile photo...
                  </div>
                )}
              </div>
              <div className={styles.usernameContainer}>
                <div className={styles.usernamePill}>
                  <div className={styles.usernamePillText}>
                    {userData?.username || '@Username'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bio Section */}
          <div className={styles.bioSection}>
            <BioContainer>
              {userData?.bio || 'No bio provided.'}
            </BioContainer>
          </div>
          
          {/* Edit Profile Button */}
          <div className={styles.editProfileContainer}>
            <button 
              onClick={() => navigate('/edit-profile')} 
              className={styles.editProfileButton}
            >
              Edit Profile
            </button>
          </div>
        </>
      )}
    </div>
  );
};

// Wrap the component with ErrorBoundary
const ProfilePage = () => (
  <ErrorBoundary>
    <ProfilePageContent />
  </ErrorBoundary>
);

export default ProfilePage;
