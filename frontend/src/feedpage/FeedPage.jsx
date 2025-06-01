import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useSharedMatch } from '../context/SharedMatchContext';
import API_BASE_URL from '../config/api';
import './components/MatchPostCardAnimation.css'; // Import the animation CSS
import { toast, Toaster } from 'react-hot-toast';
import SearchResult from '../searchPage/SearchResult';
import { useNavigate } from 'react-router-dom';
import ErrorBoundary from '../components/ErrorBoundary';
import LazyImage from '../components/LazyImage';
import styles from './FeedPage.module.css';

// Match Post Components
import MatchPostContainer from './components/matchpostcontainer';
import MatchPostImageBorder from './components/matchpostimageborder';
import MatchPostAvatar from './components/matchpostavatar';
import MatchPostInputField from './components/matchpostInputField';
import MatchPostLikeButton from './components/matchpostlikebutton';
import MatchPostLikeCount from './components/matchpostlikecount';
import LookalikesConnectedBanner from './components/theselookalikesconnectedbanner';
import CreatePostModal from './components/CreatePostModal';
import MatchPostCard from './components/MatchPostCard';

const MOBILE_BREAKPOINT = 768;

const FeedPageContent = () => {
  const { sharedMatches } = useSharedMatch();
  const [posts, setPosts] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [lastFetchTime, setLastFetchTime] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [allPosts, setAllPosts] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const userFetchAttempts = useRef(0);
  const userCacheTimeout = useRef(null);
  const feedCacheTimeout = useRef(null);
  const navigate = useNavigate();

  // Cache timeouts (in milliseconds)
  const USER_CACHE_TIME = 300000; // 5 minutes
  const FEED_CACHE_TIME = 300000; // 5 minutes

  // Calculate backoff time based on retry count
  const getBackoffTime = useCallback((count) => {
    return Math.min(1000 * Math.pow(2, count), 300000); // Max 5 minutes
  }, []);

  // Get current user data with aggressive caching
  const fetchCurrentUser = useCallback(async (force = false) => {
    const now = Date.now();
    const lastUserFetch = localStorage.getItem('lastUserFetch');
    const cachedUser = localStorage.getItem('cachedUser');
    
    // Use cached data if available and not expired
    if (!force && lastUserFetch && (now - parseInt(lastUserFetch)) < 3600000) { // 1 hour cache
      if (cachedUser) {
        try {
          const parsedUser = JSON.parse(cachedUser);
          setCurrentUser(parsedUser);
          return;
        } catch (e) {
          console.error('Error parsing cached user:', e);
          localStorage.removeItem('cachedUser');
          localStorage.removeItem('lastUserFetch');
        }
      }
    }

    // Don't attempt to fetch if we've exceeded max attempts
    if (userFetchAttempts.current >= 3) {
      console.log('Max user fetch attempts reached, using cached data');
      if (cachedUser) {
        try {
          setCurrentUser(JSON.parse(cachedUser));
        } catch (e) {
          console.error('Error parsing cached user:', e);
        }
      }
      return;
    }

    try {
      userFetchAttempts.current += 1;
      const response = await fetch(`${API_BASE_URL}/api/users/current`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (response.status === 429) {
        console.log('Rate limit hit for user data, using cached data');
        if (cachedUser) {
          try {
            setCurrentUser(JSON.parse(cachedUser));
          } catch (e) {
            console.error('Error parsing cached user:', e);
          }
        }
        return;
      }

      if (response.ok) {
        const userData = await response.json();
        if (userData.user) {
          setCurrentUser(userData.user);
          // Cache the user data
          localStorage.setItem('cachedUser', JSON.stringify(userData.user));
          localStorage.setItem('lastUserFetch', now.toString());
          userFetchAttempts.current = 0; // Reset attempts on success
        }
      }
    } catch (err) {
      console.error('Error fetching current user:', err);
      // Use cached data on error
      if (cachedUser) {
        try {
          setCurrentUser(JSON.parse(cachedUser));
        } catch (e) {
          console.error('Error parsing cached user:', e);
        }
      }
    }
  }, []);

  // Main function to fetch feed data with retry logic and caching
  const fetchPosts = useCallback(async (isRetry = false) => {
    if (loading) return;

    const now = Date.now();
    const timeSinceLastFetch = now - lastFetchTime;
    const backoffTime = getBackoffTime(retryCount);

    if (isRetry && timeSinceLastFetch < backoffTime) {
      const waitTime = Math.ceil((backoffTime - timeSinceLastFetch) / 1000);
      setError(`Please wait ${waitTime} seconds before trying again.`);
      return;
    }

    // Check cache first
    const lastFeedFetch = localStorage.getItem('lastFeedFetch');
    if (!isRetry && lastFeedFetch && (now - parseInt(lastFeedFetch)) < FEED_CACHE_TIME) {
      const cachedPosts = localStorage.getItem('cachedPosts');
      if (cachedPosts) {
        try {
          const parsedPosts = JSON.parse(cachedPosts);
          setPosts(parsedPosts);
          return;
        } catch (e) {
          console.error('Error parsing cached posts:', e);
        }
      }
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/social/feed/`, { 
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : backoffTime;
        setRetryCount(prev => prev + 1);
        setLastFetchTime(now);
        throw new Error(`Rate limit exceeded. Please try again in ${Math.ceil(waitTime/1000)} seconds.`);
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API Error: ${response.status} - ${errorData.message || response.statusText}`);
      }

      const data = await response.json();
      
      if (!data || !Array.isArray(data.posts)) {
        console.error('Invalid feed data structure:', data);
        throw new Error('Invalid feed data format received from server');
      }
      
      const processedPosts = (data.posts || []).map(post => {
        try {
          // Use the unified match_card for match posts
          let matchCard = post.match_card || null;
          return {
            ...post,
            matchCard,
            // For match posts, extract similarity from content if needed
            is_match_post: post.is_match_post,
            // Ensure user object exists and has required fields
            user: {
              username: post.username || post.user?.username || 'unknown',
              profile_image_url: post.profile_image_url || post.user?.profile_image_url || '/static/images/default_profile.svg'
            },
            // Use backend-provided match image URL for match posts
            match_image: matchCard ? matchCard.image : (post.match_face_image_url || '/static/images/default_match.png'),
            // Make sure like and comment counts are numbers
            likes_count: post.likes_count || 0,
            comments_count: post.comments_count || 0,
            // Ensure comments array exists with properly formatted user data
            comments: Array.isArray(post.comments) ? post.comments : []
          };
        } catch (e) {
          console.error('Error processing post:', e);
          return post;
        }
      }).filter(Boolean); // Remove any null/undefined posts
      
      setPosts(processedPosts);
      setRetryCount(0);
      setLastFetchTime(now);
      
      // Cache the processed posts
      localStorage.setItem('cachedPosts', JSON.stringify(processedPosts));
      localStorage.setItem('lastFeedFetch', now.toString());
    } catch (err) {
      console.error("Failed to fetch feed:", err);
      setError(err.message || "Could not load feed data. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, [loading, lastFetchTime, retryCount, getBackoffTime]);
  
  // Format image URL helper function
  const formatImageUrl = (url, isMatchImage = false) => {
    if (!url || typeof url !== 'string') return null;
    if (url.startsWith('http') || url.startsWith('/')) return url;
    if (isMatchImage) {
      return url.includes('extracted_faces/') ? url : `/static/extracted_faces/${url}`;
    }
    return `/static/profile_pics/${url}`; // Default path for profile images
  };

  // Process posts to ensure consistent format
  const processPosts = (posts) => {
    return posts.map(post => {
      // Ensure post has required fields
      if (!post) return null;
      
      // Extract similarity from content if available
      let similarity = 0;
      if (post.similarity) {
        similarity = typeof post.similarity === 'number' ? 
          post.similarity : 
          parseFloat(post.similarity) || 0;
      } else if (post.content) {
        const match = post.content.match(/(\d+)%/);
        if (match) {
          similarity = parseFloat(match[1]);
        }
      }
      
      // Check if this is a match post
      const isMatchPost = post.content?.includes('doppelganger') || post.is_match_post || false;
      
      // Format user data
      const userData = {
        username: post.username || post.user?.username || 'unknown',
        profile_image_url: post.user?.profile_image_url || post.profile_image_url || 
                         post.user?.profile_image || post.profile_image || 
                         '/static/images/default_profile.svg'
      };
      
      // Format match image
      let matchImage = null;
      if (isMatchPost) {
        matchImage = post.match_image || 
                    post.face_filename || 
                    (post.content?.match(/#(\S+\.(?:jpg|jpeg|png|gif))\b/)?.[1]);
      }
      
      return {
        ...post,
        id: post.id || `post-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        content: post.content || '',
        username: userData.username,
        user: userData,
        match_image: matchImage ? formatImageUrl(matchImage, true) : null,
        created_at: post.created_at || new Date().toISOString(),
        likes_count: post.likes_count || 0,
        comments_count: post.comments_count || 0,
        user_has_liked: post.user_has_liked || false,
        comments: post.comments || [],
        is_match_post: isMatchPost,
        similarity: similarity
      };
    }).filter(Boolean); // Remove any null/undefined posts
  };

  // Combine API posts with shared matches
  useEffect(() => {
    // Process API posts to ensure consistent format
    const processedApiPosts = processPosts(posts || []);
    
    // Process shared matches if any
    const processedSharedMatches = (sharedMatches || []).map(match => ({
      id: match.id || `match-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content: `I found my historical doppelganger with ${Math.round(parseFloat(match.similarity || 0) * 100)}% similarity!`,
      username: match.user?.username || 'User',
      user: {
        profile_image_url: formatImageUrl(match.user_image) || '/static/images/default_profile.svg',
        username: match.user?.username || 'User'
      },
      match_image: formatImageUrl(match.match_image, true),
      created_at: match.created_at || new Date().toISOString(),
      likes_count: match.likes_count || 0,
      comments_count: match.comments_count || 0,
      user_has_liked: match.user_has_liked || false,
      comments: match.comments || [],
      is_match_post: true,
      similarity: parseFloat(match.similarity || 0) * 100
    }));
    
    // Combine and sort posts
    const combined = [
      ...processedApiPosts,
      ...processedSharedMatches
    ].sort((a, b) => {
      const dateA = new Date(a.created_at || 0);
      const dateB = new Date(b.created_at || 0);
      return dateB - dateA; // Newest first
    });
    
    setAllPosts(combined);
  }, [posts, sharedMatches]);

  useEffect(() => {
    // Initial data fetch
    fetchCurrentUser();
    fetchPosts();
    
    // Set up periodic refresh with cache consideration
    const refreshInterval = setInterval(() => {
      const now = Date.now();
      const lastFeedFetch = localStorage.getItem('lastFeedFetch');
      
      if (!lastFeedFetch || (now - parseInt(lastFeedFetch)) >= FEED_CACHE_TIME) {
        fetchPosts();
      }
    }, FEED_CACHE_TIME);
    
    const handleResize = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      clearInterval(refreshInterval);
      if (userCacheTimeout.current) clearTimeout(userCacheTimeout.current);
      if (feedCacheTimeout.current) clearTimeout(feedCacheTimeout.current);
    };
  }, [fetchCurrentUser, fetchPosts]);

  // Manual refresh handler
  const handleManualRefresh = useCallback(() => {
    fetchPosts(true);
  }, [fetchPosts]);

  // Enhanced error handling for data fetching
  const handleFetchError = useCallback((error, context) => {
    console.error(`Error in ${context}:`, error);
    const errorMessage = error.message || `Failed to ${context.toLowerCase()}`;
    setError(errorMessage);
    toast.error(errorMessage);
  }, []);

  // Enhanced image error handling
  const handleImageError = useCallback((e, postId) => {
    console.error(`Failed to load image for post ${postId}:`, e.target.src);
    e.target.style.display = 'none';
    const fallbackDiv = document.createElement('div');
    fallbackDiv.style.cssText = `
      width: 100%;
      height: 200px;
      background: #f0f0f0;
      color: #666;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      border: 2px solid #e0e0e0;
    `;
    fallbackDiv.textContent = 'Image not available';
    e.target.parentNode.appendChild(fallbackDiv);
  }, []);

  // Enhanced like handling with error boundary
  const handleLike = useCallback(async (postId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/social/feed/like_post/${postId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to like post');
      }

      const data = await response.json();
      if (data.success) {
        setPosts(prevPosts => prevPosts.map(post => 
          post.id === postId 
            ? { ...post, likes_count: data.likes_count, user_has_liked: data.user_has_liked }
            : post
        ));
        localStorage.setItem('cachedPosts', JSON.stringify(posts));
      }
    } catch (error) {
      handleFetchError(error, 'like post');
    }
  }, [handleFetchError, posts]);

  // Enhanced comment handling with error boundary
  const handleCommentSubmit = useCallback(async (postId, commentText) => {
    try {
      const formData = new FormData();
      formData.append('content', commentText);

      const response = await fetch(`${API_BASE_URL}/social/feed/comment/${postId}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `Failed to add comment: ${response.status}`);
      }
      
      if (data.success && data.comment) {
        setPosts(prevPosts => prevPosts.map(post => {
          if (post.id === postId) {
            const updatedComments = [...(post.comments || []), data.comment];
            return {
              ...post,
              comments: updatedComments,
              comments_count: updatedComments.length
            };
          }
          return post;
        }));
        
        localStorage.setItem('cachedPosts', JSON.stringify(posts));
        toast.success('Comment added successfully');
        return data;
      }
      throw new Error(data.error || 'Failed to add comment');
    } catch (error) {
      handleFetchError(error, 'add comment');
      throw error;
    }
  }, [handleFetchError, posts]);

  // Enhanced delete handling with error boundary
  const handleDeletePost = useCallback(async (postId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/social/feed/delete_post/${postId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to delete post');
      }

      const data = await response.json();
      if (data.message) {
        setPosts(prevPosts => prevPosts.filter(post => post.id !== postId));
        setAllPosts(prevPosts => prevPosts.filter(post => post.id !== postId));
        toast.success('Post deleted successfully');
      }
    } catch (error) {
      handleFetchError(error, 'delete post');
    }
  }, [handleFetchError]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}></div>
        <p>Loading feed...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error Loading Feed</h2>
        <p>{error}</p>
        <button
          onClick={handleManualRefresh}
          className={styles.retryButton}
        >
          Retry
        </button>
      </div>
    );
  }

  if (allPosts.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <h2>No Posts Yet</h2>
        <p>Be the first to share a match!</p>
        <button
          onClick={() => navigate('/search')}
          className={styles.searchButton}
        >
          Find Matches
        </button>
      </div>
    );
  }

  return (
    <div className={styles.feedContainer}>
      {allPosts.map((post) => (
        post.is_match_post ? (
          <ErrorBoundary key={post.id}>
            <MatchPostCard 
              post={post} 
              onLike={handleLike}
              onComment={handleCommentSubmit}
              onDelete={handleDeletePost}
              onImageError={(e) => handleImageError(e, post.id)}
            />
          </ErrorBoundary>
        ) : null
      ))}
    </div>
  );
};

// Wrap the component with ErrorBoundary
const FeedPage = () => (
  <ErrorBoundary>
    <FeedPageContent />
  </ErrorBoundary>
);

export default FeedPage;
