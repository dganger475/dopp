import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import SearchResult from '../../searchPage/SearchResult';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHeart, faComment, faTrash } from '@fortawesome/free-solid-svg-icons';
import ErrorBoundary from '../../components/ErrorBoundary';
import LazyImage from '../../components/LazyImage';
import styles from './MatchPostCard.module.css';

// Helper function to get match badge color based on percentage
const getMatchColor = (similarity) => {
  try {
    const percent = typeof similarity === 'number' ? similarity : parseFloat(similarity);
    
    if (percent >= 80) return '#22c55e'; // Green for high matches (80%+)
    if (percent >= 51) return '#f59e0b'; // Yellow for medium-high matches (51-79%)
    if (percent >= 31) return '#f97316'; // Orange for medium matches (31-50%)
    return '#ef4444'; // Red for low matches (0-30%)
  } catch (error) {
    console.error('Error calculating match color:', error);
    return '#ef4444'; // Default to red on error
  }
};

// Helper function to format image URL
const formatImageUrl = (url, isMatchImage = false) => {
  if (!url || typeof url !== 'string') return '/static/images/default_profile.svg';
  
  try {
    // If it's already a full URL or starts with /static/, return as is
    if (url.startsWith('http') || url.startsWith('/static')) {
      return url;
    }
    
    // For match images
    if (isMatchImage) {
      return url.includes('extracted_faces/') ? url : `/static/extracted_faces/${url}`;
    }
    
    // For profile images
    if (url.includes('profile_pics/')) {
      return url;
    }
    
    // If it's just a filename, construct the appropriate path
    return `/static/profile_pics/${url}`;
  } catch (error) {
    console.error('Error formatting image URL:', error);
    return '/static/images/default_profile.svg';
  }
};

const MatchPostCardContent = ({ post, onLike, onComment, onDelete, onImageError }) => {
  const [isLiking, setIsLiking] = useState(false);
  const [isCommenting, setIsCommenting] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [error, setError] = useState(null);

  const handleLike = useCallback(async () => {
    if (isLiking) return;
    try {
      setIsLiking(true);
      setError(null);
      await onLike(post.id);
    } catch (err) {
      setError('Failed to like post. Please try again.');
      console.error('Error liking post:', err);
    } finally {
      setIsLiking(false);
    }
  }, [isLiking, onLike, post.id]);

  const handleComment = useCallback(async (e) => {
    e.preventDefault();
    if (isCommenting || !commentText.trim()) return;
    
    try {
      setIsCommenting(true);
      setError(null);
      await onComment(post.id, commentText.trim());
      setCommentText('');
    } catch (err) {
      setError('Failed to add comment. Please try again.');
      console.error('Error adding comment:', err);
    } finally {
      setIsCommenting(false);
    }
  }, [isCommenting, onComment, post.id, commentText]);

  const handleDelete = useCallback(async () => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;
    
    try {
      setError(null);
      await onDelete(post.id);
    } catch (err) {
      setError('Failed to delete post. Please try again.');
      console.error('Error deleting post:', err);
    }
  }, [onDelete, post.id]);

  const handleImageError = useCallback((e) => {
    if (onImageError) {
      onImageError(e, post.id);
    }
  }, [onImageError, post.id]);

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorMessage}>{error}</p>
        <button 
          onClick={() => setError(null)}
          className={styles.retryButton}
        >
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <div className={styles.postCard}>
      <div className={styles.postHeader}>
        <div className={styles.userInfo}>
          <LazyImage
            src={post.user?.profile_image_url}
            alt={post.username}
            className={styles.profileImage}
            onError={handleImageError}
          />
          <span className={styles.username}>{post.username}</span>
        </div>
        <button 
          onClick={handleDelete}
          className={styles.deleteButton}
          title="Delete post"
        >
          <FontAwesomeIcon icon={faTrash} />
        </button>
      </div>

      <div className={styles.postContent}>
        <LazyImage
          src={post.match_image}
          alt="Match"
          className={styles.matchImage}
          onError={handleImageError}
        />
        <p className={styles.postText}>{post.content}</p>
      </div>

      <div className={styles.postActions}>
        <button
          onClick={handleLike}
          className={`${styles.actionButton} ${post.user_has_liked ? styles.liked : ''}`}
          disabled={isLiking}
        >
          <FontAwesomeIcon icon={faHeart} />
          <span>{post.likes_count}</span>
        </button>
        <button
          onClick={() => setIsCommenting(!isCommenting)}
          className={styles.actionButton}
        >
          <FontAwesomeIcon icon={faComment} />
          <span>{post.comments_count}</span>
        </button>
      </div>

      {isCommenting && (
        <form onSubmit={handleComment} className={styles.commentForm}>
          <input
            type="text"
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="Write a comment..."
            className={styles.commentInput}
            disabled={isCommenting}
          />
          <button
            type="submit"
            className={styles.commentButton}
            disabled={isCommenting || !commentText.trim()}
          >
            Post
          </button>
        </form>
      )}

      {post.comments && post.comments.length > 0 && (
        <div className={styles.commentsList}>
          {post.comments.map((comment) => (
            <div key={comment.id} className={styles.comment}>
              <LazyImage
                src={comment.user?.profile_image_url}
                alt={comment.username}
                className={styles.commentProfileImage}
                onError={handleImageError}
              />
              <div className={styles.commentContent}>
                <span className={styles.commentUsername}>{comment.username}</span>
                <p className={styles.commentText}>{comment.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Wrap the component with ErrorBoundary
const MatchPostCard = (props) => (
  <ErrorBoundary>
    <MatchPostCardContent {...props} />
  </ErrorBoundary>
);

export default MatchPostCard;
