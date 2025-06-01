import React, { createContext, useState, useContext, useEffect } from 'react';

const SharedMatchContext = createContext();

export const useSharedMatch = () => useContext(SharedMatchContext);

export const SharedMatchProvider = ({ children }) => {
  const [sharedMatches, setSharedMatches] = useState([]);
  
  // Add a match to the shared matches list
  const shareMatch = (matchData, userImageUrl, similarityPercentage) => {
    // Use the full image path for proper display
    let matchImage = matchData.image || matchData.filename;
    
    // Ensure the image path is properly formatted
    if (matchImage) {
      // If it's a relative path, make it absolute
      if (!matchImage.startsWith('http') && !matchImage.startsWith('/')) {
        matchImage = `/${matchImage}`;
      }
      // If it doesn't include the extracted_faces directory, add it
      if (!matchImage.includes('extracted_faces') && !matchImage.startsWith('http')) {
        matchImage = matchImage.startsWith('/') ? `/static/extracted_faces${matchImage}` : `/static/extracted_faces/${matchImage}`;
      }
    }
    
    // Ensure we have a valid user image URL
    const processedUserImage = userImageUrl || '/static/images/default_profile.svg';
    
    // Create the new match object
    const newMatch = {
      id: `temp-${Date.now()}`, // Temporary ID until backend assigns one
      content: `I found my historical doppelganger with ${similarityPercentage ? Math.round(parseFloat(similarityPercentage) * 100) : 0}% similarity!`,
      user_image: processedUserImage,
      username: 'realkeed', // Hardcoded for consistency
      user: {
        profile_image_url: processedUserImage,
        username: 'realkeed'
      },
      match_image: matchImage,
      similarity: similarityPercentage,
      is_match_post: true,
      created_at: new Date().toISOString(),
      decade: matchData.decade,
      state: matchData.state,
      timestamp: Date.now()
    };
    
    console.log('Sharing match with image:', matchImage);
    setSharedMatches(prev => [newMatch, ...prev]);
    return newMatch;
  };
  
  // Clear a shared match after it's been properly saved to the backend
  const clearSharedMatch = (matchId) => {
    setSharedMatches(prev => prev.filter(match => match.id !== matchId));
  };
  
  const value = {
    sharedMatches,
    shareMatch,
    clearSharedMatch
  };
  
  return (
    <SharedMatchContext.Provider value={value}>
      {children}
    </SharedMatchContext.Provider>
  );
};

export default SharedMatchContext;
