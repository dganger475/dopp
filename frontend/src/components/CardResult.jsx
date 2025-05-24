import React, { useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

// Helper function to get match badge color based on percentage
const getMatchColor = (similarity) => {
  const percent = parseFloat(similarity) * 100;
  
  if (percent >= 90) return '#22c55e'; // Green for high matches
  if (percent >= 70) return '#3b82f6'; // Blue for good matches
  if (percent >= 50) return '#f59e0b'; // Yellow/amber for medium matches
  return '#ef4444'; // Red for low matches
};

const CardResult = ({ result, index, isActive }) => {
  const badgeRef = useRef(null);
  
  // Handle badge animation when active state changes
  useEffect(() => {
    if (badgeRef.current) {
      if (isActive) {
        // Fade in the badge when this card becomes active
        badgeRef.current.style.opacity = '0';
        badgeRef.current.style.transform = 'scale(0.7) translateX(10px)';
        
        // Small delay to ensure the transition is visible
        setTimeout(() => {
          badgeRef.current.style.opacity = '1';
          badgeRef.current.style.transform = 'scale(1) translateX(0)';
        }, 50);
      } else {
        // Fade out the badge when this card is no longer active
        badgeRef.current.style.opacity = '0';
        badgeRef.current.style.transform = 'scale(0.7) translateX(10px)';
      }
    }
  }, [isActive]);

  // Determine if this is a registered user
  const dataSource = result.data_source;
  const hasUserIds = result.registered_user_id || result.claimed_by_user_id;
  const isRegisteredFlag = result.is_registered === true || result.is_registered === "true";
  const filenameIndicatesUser = result.original_filename && result.original_filename.startsWith('userprofile_');
  
  const isRegistered = dataSource === "users_table" || hasUserIds || isRegisteredFlag || filenameIndicatesUser;
  
  // Force a proper username display for registered users
  let displayUsername = 'Unclaimed Profile';
  
  if (isRegistered) {
    // For registered users, ALWAYS show @Profile #103
    displayUsername = '@Profile #103';
    
    // Log all possible username fields for debugging
    console.log('Username debugging:', {
      rawUsername: result.username,
      raw: result,
      finalDisplay: displayUsername
    });
  }
  
  // Card styling based on user type
  const cardBgColor = isRegistered ? '#ef4444' : '#007bff'; // Red for registered, blue for unclaimed
  // Top pill text (always standard labels)
  const labelText = isRegistered ? 'REGISTERED USER' : 'UNCLAIMED PROFILE';
  
  return (
    <div 
      key={result.id || result.filename || index}
      className="result-card"
      style={{
        width: '140px',
        height: '240px',
        backgroundColor: cardBgColor,
        borderRadius: '6px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        padding: '12px 4px 8px 4px',
        margin: '0 4px',
        boxSizing: 'border-box',
        flexShrink: 0,
        color: '#fff',
        scrollSnapAlign: 'start', /* Make this element a snap point */
        scrollSnapStop: 'always', /* Force scrolling to stop at this element */
        animation: `fadeIn 0.5s ease forwards ${index * 0.1}s`,
        opacity: 0,
        transform: 'translateY(10px)'
      }}
    >
      {/* Label at top */}
      <div style={{
        width: '130px',
        height: '24px',
        backgroundColor: isRegistered ? '#000000' : '#000000', // Black for both
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
        }}>{labelText}</span>
      </div>
      
      {/* Image container */}
      <div style={{ marginTop: '36px', width: '108px', height: '108px', position: 'relative' }}>
        <div style={{
          width: '108px',
          height: '108px',
          border: isRegistered ? '5.3px solid #000000' : '5.3px solid #000000', // Black border for both
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden', // Make sure the image stays inside the border
          boxSizing: 'border-box', // Include border in the width/height calculation
          padding: '0', // No padding to maximize image space
        }}>
          {/* Hard-coded image paths based on the screenshot */}
          <img
            src={isRegistered ? 
                 "http://localhost:5000/static/images/default_profile.jpg" : 
                 "http://localhost:5000/static/images/unclaimed_profile.jpg"}
            alt={'Profile Image'}
            style={{ 
              width: '95px', // Fixed width to ensure it stays inside border
              height: '95px', // Fixed height to ensure it stays inside border
              borderRadius: '2px', 
              objectFit: 'cover',
              backgroundColor: '#f0f0f0', /* Light background if image is transparent */
              margin: '0 auto', // Center the image
              border: 'none' // No additional border on the image itself
            }}
          />
        </div>
      </div>
      
      {/* Username for registered users only */}
      {isRegistered && (
        <div style={{
          marginTop: '8px',
          width: 'auto',
          minWidth: '96px',
          maxWidth: '120px',
          height: '24px',
          backgroundColor: '#000000', // Black for registered
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
          }}>@Profile #103</span>
        </div>
      )}
      
      {/* Location Information */}
      {isRegistered ? (
        // For registered users - show city/state only
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
          {(result.currentCity || result.city) || 
            <span style={{ fontStyle: 'italic', color: '#dddddd' }}>Location N/A</span>}
        </div>
      ) : (
        // For non-registered users - show state and decade with specific styling
        <div style={{
          marginTop: '18px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '4px',
        }}>
          {/* State */}
          <div style={{
            color: '#000000',
            fontSize: '12px',
            fontFamily: 'Arial, sans-serif',
            fontWeight: 'bold',
            textAlign: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.85)',
            padding: '2px 8px',
            borderRadius: '4px',
          }}>
            {result.state || 'Unknown State'}
          </div>
          
          {/* Decade */}
          <div style={{
            color: '#000000',
            fontSize: '12px',
            fontFamily: 'Arial, sans-serif',
            fontWeight: 'bold',
            textAlign: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.85)',
            padding: '2px 8px',
            borderRadius: '4px',
          }}>
            {result.decade || 'Unknown Decade'}
          </div>
        </div>
      )}
      
      {/* Match Percentage Badge */}
      {result.similarity && (
        <div style={{
          position: 'absolute',
          top: '40%',
          right: '-18px',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '11px',
          fontFamily: 'Arial, sans-serif',
          backgroundColor: getMatchColor(result.similarity),
          border: '2px solid white',
          color: '#fff',
          boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
          zIndex: 5
        }}>
          {Math.round(parseFloat(result.similarity) * 100)}%
        </div>
      )}
    </div>
  );
};

export default CardResult;
