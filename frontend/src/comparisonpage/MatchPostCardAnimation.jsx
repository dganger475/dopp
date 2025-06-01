import React from 'react';

// Helper function to get match badge color based on percentage
const getMatchColor = (similarity) => {
  const percent = typeof similarity === 'number' ? similarity : parseFloat(similarity);
  
  if (percent >= 90) return '#22c55e'; // Green for high matches
  if (percent >= 70) return '#3b82f6'; // Blue for good matches
  if (percent >= 50) return '#f59e0b'; // Yellow/amber for medium matches
  return '#ef4444'; // Red for low matches
};

const MatchPostCardAnimation = ({ userImage, matchImage, similarity, matchId, isAnimating, username, matchUsername }) => {
  // Card styling
  const cardBgColor = '#007bff'; // Blue for match posts
  const borderColor = '#000000'; // Black border
  const labelBgColor = '#000000'; // Black label
  const labelTextColor = '#ffffff'; // White text
  const labelText = 'MATCH FOUND';
  
  // Calculate similarity percentage
  const similarityPercentage = similarity ? 
    (typeof similarity === 'number' ? 
      (similarity <= 1 ? Math.round(similarity * 100) : Math.round(similarity)) : 
      (parseFloat(similarity) <= 1 ? Math.round(parseFloat(similarity) * 100) : Math.round(parseFloat(similarity)))) : 
    0;
  
  return (
    <div className={`match-post-card ${isAnimating ? 'animate-share' : ''}`} style={{
      width: '100%',
      maxWidth: '600px',
      backgroundColor: cardBgColor,
      borderRadius: '12px',
      border: 'none',
      boxShadow: 'rgba(0, 0, 0, 0.4) 0px 12px 32px, rgba(0, 0, 0, 0.3) 0px 6px 16px, rgba(0, 0, 0, 0.2) 0px 3px 8px',
      margin: '24px auto 16px auto',
      padding: '16px',
      fontFamily: 'Arial, sans-serif',
      position: 'relative',
      color: '#fff',
      transition: 'all 0.5s ease',
      animation: isAnimating ? 'shareToFeed 2.5s forwards' : 'none',
    }}>
      {/* Author avatar in top left */}
      <div style={{
        position: 'absolute',
        top: '8px',
        left: '8px',
        width: '28px',
        height: '28px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        zIndex: 3,
        border: 'none',
        boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
      }}>
        {userImage ? (
          <div style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#333'
          }}>
            <img
              src={userImage}
              alt="Author"
              style={{
                maxWidth: '90%',
                maxHeight: '90%',
                objectFit: 'contain'
              }}
            />
          </div>
        ) : (
          <div style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#444',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '10px'
          }}>
            R
          </div>
        )}
      </div>
      {/* Banner at top */}
      <div style={{
        width: '80%',
        height: '32px',
        backgroundColor: labelBgColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        marginBottom: '8px',
        marginLeft: 'auto',
        marginRight: 'auto',
        borderRadius: '8px',
        zIndex: 2,
        border: 'none',
        boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
      }}>
        <span style={{ 
          color: labelTextColor,
          fontSize: '16px', 
          fontWeight: 'bold',
          fontFamily: 'Arial, sans-serif',
          whiteSpace: 'nowrap',
          letterSpacing: '1px'
        }}>{labelText}</span>
      </div>
      
      {/* Images container */}
      <div style={{ 
        marginTop: '6px', 
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        padding: '0 12px',
        gap: '20px'
      }}>
          {/* User image with username label */}
          <div style={{
            width: '110px',
            height: '100px',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
          }}>
            <div style={{
              width: '110px',
              height: '90px',
              border: 'none',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              boxSizing: 'border-box',
              padding: '0px',
              margin: '0px',
              backgroundColor: '#000000',
              boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
            }}>
              {userImage ? (
                <img
                  src={userImage}
                  alt="Your Face"
                  onError={(e) => {
                    console.log('User image failed to load');
                    e.target.style.display = 'none';
                  }}
                  style={{
                    width: '104px',
                    height: '84px',
                    objectFit: 'cover',
                    backgroundColor: '#f0f0f0',
                    display: 'block',
                    margin: 0,
                    border: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '104px',
                    height: '84px',
                    backgroundColor: '#444444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '9px',
                    color: '#ffffff',
                    textAlign: 'center',
                    margin: 0,
                    padding: '4px',
                    boxSizing: 'border-box',
                  }}
                >
                  No face image available
                </div>
              )}
            </div>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: 'bold', 
              textAlign: 'center',
              marginTop: '0px',
              color: '#ffffff',
              backgroundColor: '#000000',
              width: '110px',
              padding: '4px 0px',
              borderRadius: '0px 0px 8px 8px',
              border: 'none',
              boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
            }}>@{username || 'user'}</div>
          </div>
          
          {/* Match image with label */}
          <div style={{
            width: '110px',
            height: '100px',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
          }}>
            {/* Small UNCLAIMED banner */}
            <div style={{
              position: 'absolute',
              top: '-8px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#ffffff',
              color: '#000000',
              fontSize: '9px',
              fontWeight: 'bold',
              padding: '2px 6px',
              borderRadius: '4px',
              border: 'none',
              zIndex: 3,
              boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
            }}>
              UNCLAIMED
            </div>
            <div style={{
              width: '110px',
              height: '90px',
              border: 'none',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              boxSizing: 'border-box',
              padding: '0px',
              margin: '0px',
              backgroundColor: '#000000',
              boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
            }}>
              {matchImage ? (
                <img
                  src={matchImage}
                  alt="Match Face"
                  onError={(e) => {
                    console.error('Match image failed to load');
                    e.target.style.display = 'none';
                  }}
                  style={{
                    width: '104px',
                    height: '84px',
                    objectFit: 'cover',
                    backgroundColor: '#f0f0f0',
                    display: 'block',
                    margin: 0,
                    border: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '104px',
                    height: '84px',
                    backgroundColor: '#444444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '9px',
                    color: '#ffffff',
                    textAlign: 'center',
                    margin: 0,
                    padding: '4px',
                    boxSizing: 'border-box',
                  }}
                >
                  No match image available
                </div>
              )}
            </div>
            <div style={{ 
              fontSize: '11px', 
              fontWeight: 'bold', 
              textAlign: 'center',
              marginTop: '0px',
              color: '#ffffff',
              backgroundColor: '#000000',
              width: '110px',
              padding: '3px 0px',
              borderRadius: '0px 0px 8px 8px',
              border: 'none',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
            }}>{matchUsername || matchId || 'unknown'}</div>
          </div>
      </div>
      
      {/* Actions and Similarity row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        marginTop: '6px',
        marginBottom: '4px',
        padding: '0 12px',
        position: 'relative'
      }}>
        {/* Similarity percentage badge */}
        <div style={{
          backgroundColor: '#ffffff',
          color: '#000000',
          fontWeight: 'bold',
          padding: '4px 10px',
          borderRadius: '8px',
          fontSize: '14px',
          border: 'none',
          display: 'inline-block',
          textAlign: 'center',
          width: '150px',
          boxShadow: 'rgba(0, 0, 0, 0.3) 0px 8px 16px, rgba(0, 0, 0, 0.2) 0px 4px 8px'
        }}>
          <span>SIMILARITY {similarityPercentage}%</span>
        </div>
        
        {/* Like button */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            color: '#ffffff',
            fontSize: '20px',
            fontWeight: 'bold',
            marginRight: '4px',
          }}>
            🖤
          </div>
          <div style={{
            fontSize: '18px',
            fontWeight: 'bold',
            color: '#ffffff',
            marginRight: '8px'
          }}>
            0
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchPostCardAnimation;
