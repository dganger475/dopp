import React, { useState, useEffect, useRef } from 'react';
import API_BASE_URL from '../config/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons';
import CardResult from '../components/CardResult';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';

const MOBILE_BREAKPOINT = 768;

const SearchPage = () => {
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true); 
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [renderError, setRenderError] = useState(null); 
  const [showResults, setShowResults] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [activeIndex, setActiveIndex] = useState(0);
  const [buttonClicked, setButtonClicked] = useState(false);
  const carouselRef = useRef(null);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    setLoadingUser(true);
    fetch('/auth/current_user', { credentials: 'include' })
      .then(res => {
        if (!res.ok) return Promise.reject(new Error(`Failed to fetch user: ${res.status}`));
        return res.json();
      })
      .then(data => {
        // Add detailed debugging information
        console.log('Current user data (raw):', data);
        console.log('User object structure:', data.user);
        console.log('Profile image URL:', data.user?.profile_image_url);
        console.log('Username:', data.user?.username);
        
        // Set user data and also extract the nested user object for easier access
        const enhancedData = {
          ...data,
          // Extract user data to the top level for easier access
          username: data.user?.username,
          profile_image_url: data.user?.profile_image_url
        };
        
        console.log('Enhanced user data:', enhancedData);
        setUser(enhancedData);
      })
      .catch(err => {
        console.error("Failed to fetch current user:", err.message);
        setError("Could not load user data."); 
        setUser(null); 
      })
      .finally(() => {
        setLoadingUser(false);
      });
  }, []);

  // Update image paths to use the correct server URL
  const updateImagePaths = () => {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
      if (img.src.startsWith('/static/')) {
        img.src = 'http://localhost:5000' + img.src;
      }
    });
  };

  // Call updateImagePaths when the component mounts
  useEffect(() => {
    updateImagePaths();
  }, []);

  useEffect(() => {
    // Add keyboard navigation
    const handleKeyDown = (e) => {
      if (results.length === 0) return;
      
      if (e.key === 'ArrowLeft') {
        if (activeIndex > 0) {
          const newIndex = activeIndex - 1;
          navigateToCard(newIndex);
        }
      } else if (e.key === 'ArrowRight') {
        if (activeIndex < results.length - 1) {
          const newIndex = activeIndex + 1;
          navigateToCard(newIndex);
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, results]);
  
  // Function to navigate to a specific card
  const navigateToCard = (index) => {
    if (carouselRef.current) {
      const cardWidth = 140 + 16; // card width + gap
      carouselRef.current.scrollTo({
        left: index * cardWidth,
        behavior: 'smooth'
      });
      setActiveIndex(index);
    }
  };

  const performSearch = async () => {
    const searchUrl = `${API_BASE_URL}/api/search`;
    setLoading(true);
    setError(null); 
    setRenderError(null); 
    setShowResults(true);
    try {
      const response = await fetch(searchUrl, { credentials: 'include' });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      console.log("Search results received:", data.results, "total:", data.total);
      if (data.results && data.results.length > 0) {
        data.results.forEach((result, index) => {
          console.log(`Result ${index} - is_registered: ${result.is_registered}, username: ${result.username}`);
        });
        setResults(data.results);
      } else {
        console.warn("No results returned from search API");
        setResults([]);
      }
    } catch (e) {
      console.error("Failed to fetch results:", e);
      setError("Failed to fetch search results.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  if (loadingUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'var(--dopple-font)', flexDirection: 'column', gap: '20px' }}>
        <div className="loading-spinner" style={{
          width: '50px',
          height: '50px',
          border: '5px solid rgba(0, 123, 255, 0.2)',
          borderRadius: '50%',
          borderTop: '5px solid #007bff',
          animation: 'spin 1s linear infinite',
        }}></div>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
            .loading-spinner {
              width: 50px;
              height: 50px;
              border: 5px solid rgba(0, 123, 255, 0.2);
              border-radius: 50%;
              border-top: 5px solid #007bff;
              animation: spin 1s linear infinite;
            }
            @keyframes fadeIn {
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
            .result-card {
              animation: fadeIn 0.5s ease forwards;
              opacity: 0;
              transform: translateY(10px);
            }
          `}
        </style>
        <div>Loading user information...</div>
      </div>
    );
  }

  if (renderError) {
    return (
      <div style={{ padding: '20px', color: 'red', fontFamily: 'var(--dopple-font)' }}>
        <h1>Application Error</h1>
        <p>Sorry, something went wrong while trying to display this page.</p>
        <p>Error: {renderError.message}</p>
        <pre>{renderError.stack}</pre>
      </div>
    );
  }

  try {
    return (
      <div style={{ 
        background: '#f0f2f5', 
        minHeight: '100vh', 
        fontFamily: 'var(--dopple-font)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div 
          className="dopple-container dopple-search-layout"
          style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'flex-start',
            gap: '8px',
            width: '100%',
            maxWidth: '1200px',
            position: 'fixed',
            top: '156px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '20px',
            boxSizing: 'border-box',
            zIndex: 100,
            background: '#f0f2f5',
          }}
        >
          {/* Left Column: User Card and Controls */}
          <div 
            style={{ 
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '10px',
              width: '160px',
              flexShrink: 0,
              position: 'relative',
            }} 
          >
            {user && (
              <div 
                style={{
                  width: '140px',
                  height: '240px',
                  backgroundColor: '#000000',
                  borderRadius: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  position: 'relative',
                  padding: '12px 4px 8px 4px',
                  boxSizing: 'border-box',
                  color: '#fff',
                }}
              >
                {/* Label at top */}
                <div style={{
                  width: '130px',
                  height: '24px',
                  backgroundColor: '#007bff',
                  borderRadius: '9999px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'absolute',
                  top: '8px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  zIndex: 2,
                }}>
                  <span style={{ 
                    color: '#fff', 
                    fontSize: '10px', 
                    fontWeight: 'bold',
                    fontFamily: 'Arial, sans-serif',
                    whiteSpace: 'nowrap'
                  }}>YOUR CARD</span>
                </div>
                
                {/* Image container */}
                <div style={{ marginTop: '36px', width: '108px', height: '108px', position: 'relative' }}>
                  <div style={{
                    width: '108px',
                    height: '106px',
                    border: '5.3px solid #007bff',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <img
                      src={user.profile_image_url || (user.user && user.user.profile_image_url) || `${API_BASE_URL}/static/images/default_profile.jpg`}
                      alt={user.username || (user.user && user.user.username) || 'Your Profile'}
                      style={{ width: '100px', height: '100px', borderRadius: '4px', objectFit: 'cover' }}
                    />
                  </div>
                </div>
                
                {/* Username */}
                <div style={{
                  marginTop: '8px',
                  width: 'auto',
                  minWidth: '96px',
                  maxWidth: '120px',
                  height: '24px',
                  backgroundColor: '#007bff',
                  borderRadius: '9999px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 8px',
                }}>
                  <span style={{
                    color: '#fff',
                    fontSize: '12px',
                    fontFamily: 'Arial, sans-serif',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: '100px',
                    padding: '0 4px',
                  }}>{user.username || (user.user && user.user.username) || 'Your Profile'}</span>
                </div>
                
                {/* City/State */}
                <div style={{
                  marginTop: '4px',
                  color: '#fff',
                  fontSize: '11px',
                  fontFamily: 'Arial, sans-serif',
                  textAlign: 'center',
                  width: '100%',
                  maxWidth: '120px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {(user.currentCity || (user.user && user.user.city)) || 
                    <span style={{ fontStyle: 'italic', color: '#dddddd' }}>Location N/A</span>}
                </div>
              </div>
            )}
            <button
              className="dopple-bg-primary dopple-text-white dopple-rounded-lg dopple-py-3 hover:dopple-bg-primary-dark dopple-transition dopple-shadow-md find-matches-btn"
              style={{ 
                marginTop: '10px', 
                marginBottom: '0', 
                width: '140px',
                alignSelf: 'center',
                position: 'relative',
                textAlign: 'center',
                fontSize: '12px',
                fontFamily: 'Arial, sans-serif',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '6px 10px',
                transition: 'all 0.2s ease',
                overflow: 'hidden',
                backgroundColor: buttonClicked ? '#0056b3' : '#007bff',
                top: '-30px'
              }}
              onClick={(e) => {
                setButtonClicked(true);
                // Create ripple effect
                const button = e.currentTarget;
                const circle = document.createElement('span');
                const diameter = Math.max(button.clientWidth, button.clientHeight);
                const radius = diameter / 2;
                
                circle.style.width = circle.style.height = `${diameter}px`;
                circle.style.left = `${e.clientX - button.getBoundingClientRect().left - radius}px`;
                circle.style.top = `${e.clientY - button.getBoundingClientRect().top - radius}px`;
                circle.classList.add('ripple');
                
                const ripple = button.getElementsByClassName('ripple')[0];
                if (ripple) {
                  ripple.remove();
                }
                
                button.appendChild(circle);
                
                // Execute search and reset button state
                performSearch();
                setTimeout(() => setButtonClicked(false), 600);
              }}
              disabled={loading}
            >
              <style>
                {`
                  .find-matches-btn {
                    position: relative;
                    overflow: hidden;
                  }
                  .ripple {
                    position: absolute;
                    border-radius: 50%;
                    background-color: rgba(255, 255, 255, 0.4);
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                    pointer-events: none;
                  }
                  @keyframes ripple {
                    to {
                      transform: scale(4);
                      opacity: 0;
                    }
                  }
                `}
              </style>
              {loading ? 'Finding Matches...' : (results.length > 0 ? 'Find New Matches' : 'Find Matches')}
            </button>

            {error && 
              <div className="dopple-card dopple-white-border" style={{ color: 'red', padding: '15px', marginBottom: '20px', borderColor: 'red', background: '#fff8f8', width: '100%' }}>
                <strong>Error:</strong> {error}
              </div>}

          </div> {/* End of Left Column div */}

          {/* Right Column: Search Results Carousel */}
          {showResults && (
            <div style={{ 
              flex: 1,
              minWidth: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              marginTop: '0',
              border: 'none',
              position: 'relative',
              height: '240px',
              overflowY: 'hidden'
            }}>
              {loading && <LoadingState />}
              
              {!loading && !error && results.length === 0 && !isMobile && <EmptyState />}
              
              {/* Carousel with scroll indicators */}
              {results.length > 0 && (
                <div style={{ position: 'relative' }}>
                  {/* Removed left scroll indicator - only keeping right arrow */}
                  
                  {/* Right scroll indicator */}
                  {results.length > 0 && activeIndex < results.length - 1 && (
                    <div
                      onClick={() => {
                        if (carouselRef.current) {
                          const newIndex = Math.min(results.length - 1, activeIndex + 1);
                          const cardWidth = 140 + 16; // card width + gap
                          carouselRef.current.scrollTo({
                            left: newIndex * cardWidth,
                            behavior: 'smooth'
                          });
                          setActiveIndex(newIndex);
                        }
                      }}
                      style={{
                        position: 'absolute',
                        right: '0px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        cursor: 'pointer',
                        zIndex: 100,
                        transition: 'all 0.2s ease',
                        boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)'
                      }}
                    >
                      <FontAwesomeIcon icon={faChevronRight} />
                    </div>
                  )}
                  
                  {/* Card Carousel */}
                  <div
                    ref={carouselRef}
                    onScroll={(e) => {
                      if (carouselRef.current) {
                        const scrollLeft = e.currentTarget.scrollLeft;
                        const cardWidth = 140 + 16; // card width + gap
                        const newIndex = Math.round(scrollLeft / cardWidth);
                        if (newIndex !== activeIndex) {
                          setActiveIndex(newIndex);
                        }
                      }
                    }}
                    style={{
                      display: 'flex',
                      flexDirection: 'row',
                      gap: '16px',
                      overflowX: 'auto',
                      overflowY: 'hidden', /* Prevent vertical scrolling */
                      padding: '0px 10px',
                      width: '100%',
                      minHeight: '240px',
                      alignItems: 'flex-start',
                      boxSizing: 'border-box',
                      border: 'none',
                      scrollSnapType: 'x mandatory',
                      scrollBehavior: 'smooth',
                      WebkitOverflowScrolling: 'touch',
                      msOverflowStyle: 'none',
                      scrollbarWidth: 'none',
                      position: 'relative'
                    }}
                  >
                    {/* Dot indicators */}
                    <div style={{
                      position: 'absolute',
                      bottom: '-25px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      display: 'flex',
                      gap: '8px',
                      zIndex: 10
                    }}>
                      {results.map((_, idx) => (
                        <div 
                          key={`dot-${idx}`}
                          onClick={() => {
                            if (carouselRef.current) {
                              const cardWidth = 140 + 16; // card width + gap
                              carouselRef.current.scrollTo({
                                left: idx * cardWidth,
                                behavior: 'smooth'
                              });
                              setActiveIndex(idx);
                            }
                          }}
                          style={{
                            width: idx === activeIndex ? '10px' : '8px',
                            height: idx === activeIndex ? '10px' : '8px',
                            borderRadius: '50%',
                            backgroundColor: idx === activeIndex ? '#007bff' : '#ccc',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease'
                          }}
                        />
                      ))}
                    </div>

                    {/* Result Cards */}
                    {results.map((result, index) => (
                      <CardResult 
                        key={result.id || result.filename || index} 
                        result={result} 
                        index={index} 
                        isActive={index === activeIndex} 
                      />
                    ))}
                    
                    {/* Removed centralized match percentage badge - using individual badges on cards instead */}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  } catch (e) {
    console.error("Render error in SearchPage:", e);
    setRenderError(e);
    return (
      <div style={{ padding: '20px', color: 'red', fontFamily: 'var(--dopple-font)' }}>
        <h1>Application Error</h1>
        <p>Sorry, something went wrong while trying to display this page.</p>
        <p>Error: {e.message}</p>
        <pre>{e.stack}</pre>
      </div>
    );
  }
};

// Helper function to get match badge color based on percentage
const getMatchColor = (similarity) => {
  const percent = parseFloat(similarity) * 100;
  
  if (percent >= 90) return '#22c55e'; // Green for high matches
  if (percent >= 70) return '#3b82f6'; // Blue for good matches
  if (percent >= 50) return '#f59e0b'; // Yellow/amber for medium matches
  return '#ef4444'; // Red for low matches
};

export default SearchPage;
