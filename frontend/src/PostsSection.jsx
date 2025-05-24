import React, { useState, useEffect } from 'react';
import API_BASE_URL from "./config/api";
// import styles from './PostsSection.module.css'; // Optional

// Basic PostCard component (can be moved to its own file: PostCard.jsx)
const PostCard = ({ post }) => {
  // Fallback for user data if not directly available on post object
  const user = post.user || post.author || { username: 'User', profile_image_url: '/static/default_profile.png' };
  const postTimestamp = post.timestamp || post.created_at;
  
  return (
    <div className="post-card" style={{
      border: '1px solid #ddd',
      borderRadius: '8px',
      marginBottom: '20px',
      padding: '15px',
      backgroundColor: '#fff',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div className="post-header" style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
        <img 
          src={user.profile_image_url || '/static/default_profile.png'} 
          alt={user.username} 
          style={{ width: '40px', height: '40px', borderRadius: '50%', marginRight: '10px', objectFit: 'cover' }}
        />
        <div>
          <span className="post-username" style={{ fontWeight: 'bold' }}>{user.full_name || user.username}</span>
          {postTimestamp && 
            <span className="post-timestamp" style={{ display: 'block', fontSize: '0.8em', color: '#666' }}>
              {new Date(postTimestamp).toLocaleString()}
            </span>
          }
        </div>
      </div>
      {post.content && <div className="post-content" style={{ marginBottom: '10px' }}><p>{post.content}</p></div>}
      {post.image_url && <img src={post.image_url} alt="Post image" style={{ width: '100%', borderRadius: '4px', marginBottom: '10px' }}/>}
      {/* Add other post elements like likes, comments, share button if needed */}
      {post.shared_match && (
        <div className="shared-match" style={{ border: '1px solid #eee', padding: '10px', borderRadius: '4px', marginTop: '10px' }}>
          <p style={{fontWeight: 'bold', fontSize: '0.9em', marginBottom: '5px'}}>Shared Match:</p>
          {/* Basic display for shared match, can be enhanced with UniversalCard or similar */}
          <img src={post.shared_match.match_image_url || '/static/default_match.png'} alt={post.shared_match.match_name} style={{maxWidth: '100px', maxHeight: '100px', borderRadius: '4px', marginBottom: '5px'}} />
          <div>Name: {post.shared_match.match_name}</div>
          <div>Similarity: {post.shared_match.similarity ? `${Math.round(post.shared_match.similarity * 100)}%` : 'N/A'}</div>
        </div>
      )}
      <div className="post-footer" style={{marginTop: '10px', borderTop: '1px solid #eee', paddingTop: '10px'}}>
        {/* Placeholder for actions like Like, Comment, Share */}
        <button style={{marginRight: '10px'}}>Like ({post.likes_count || 0})</button>
        <button>Comment ({post.comments_count || 0})</button>
      </div>
    </div>
  );
};

const PostsSection = ({ userId, isCurrentUser }) => {
  const [posts, setPosts] = useState([]);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [postsError, setPostsError] = useState(null);

  useEffect(() => {
    if (!userId) {
      setLoadingPosts(false);
      setPostsError("User ID is not provided.");
      return;
    }

    const fetchUserPosts = async () => {
      setLoadingPosts(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/posts`, {
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch posts (status: ${response.status})`);
        }
        const data = await response.json();
        setPosts(data.posts || data || []);
      } catch (err) {
        setPostsError(err.message);
      } finally {
        setLoadingPosts(false);
      }
    };

    fetchUserPosts();
  }, [userId]);

  if (loadingPosts) {
    return <div className="loading-placeholder" style={{textAlign: 'center', padding: '20px'}}>Loading posts...</div>;
  }

  if (postsError) {
    return <div className="error-placeholder" style={{textAlign: 'center', padding: '20px', color: 'red'}}>Error loading posts: {postsError}</div>;
  }

  if (posts.length === 0) {
    return (
      <div className="empty-placeholder" style={{textAlign: 'center', padding: '40px'}}>
        <p>{isCurrentUser ? "You haven't" : "This user hasn't"} posted anything yet.</p>
        {isCurrentUser && 
          <button 
            onClick={() => {/* Logic to open create post modal or navigate */}}
            style={{padding: '10px 20px', backgroundColor: 'var(--dopple-purple)', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', marginTop: '10px'}}
          >
            Create Your First Post
          </button>
        }
      </div>
    );
  }

  return (
    <div /*className={styles.postsList}*/>
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
};

export default PostsSection;
