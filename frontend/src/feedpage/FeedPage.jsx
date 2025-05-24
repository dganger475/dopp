import React, { useEffect, useState } from 'react';
import NavBar from '../components/NavBar';

// Match Post Components
import MatchPostContainer from './components/matchpostcontainer';
import MatchPostImageBorder from './components/matchpostimageborder';
import MatchPostAvatar from './components/matchpostavatar';
import MatchPostInputField from './components/matchpostInputField';
import MatchPostLikeButton from './components/matchpostlikebutton';
import MatchPostLikeCount from './components/matchpostlikecount';
import LookalikesConnectedBanner from './components/theselookalikesconnectedbanner';
import CreatePostModal from './components/CreatePostModal';

const MOBILE_BREAKPOINT = 768;

const FeedPage = () => {
  const [posts, setPosts] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const response = await fetch('/social/feed/', { 
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch feed: ${response.status}`);
      }
      
      const data = await response.json();
      setPosts(data.posts || []);
    } catch (err) {
      console.error("Failed to fetch feed:", err.message);
      setError("Could not load feed data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handleResize);
    fetchPosts();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLike = async (postId) => {
    try {
      const response = await fetch(`/social/feed/like/${postId}`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to like post');
      }

      const data = await response.json();
      if (data.success) {
        setPosts(posts.map(post => {
          if (post.id === postId) {
            return {
              ...post,
              likes_count: post.user_has_liked ? post.likes_count - 1 : post.likes_count + 1,
              user_has_liked: !post.user_has_liked
            };
          }
          return post;
        }));
      }
    } catch (err) {
      console.error('Error liking post:', err);
    }
  };

  const handleComment = async (postId, comment) => {
    try {
      const formData = new FormData();
      formData.append('content', comment);

      const response = await fetch(`/social/feed/comment/${postId}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to add comment');
      }

      const data = await response.json();
      if (data.success) {
        // Refresh the posts to show the new comment
        fetchPosts();
      }
    } catch (err) {
      console.error('Error adding comment:', err);
    }
  };

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

  return (
    <div style={{ background: '#f0f2f5', minHeight: '100vh', fontFamily: 'var(--dopple-font)' }}>
      <div style={{ paddingTop: '64px', paddingBottom: '80px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', maxWidth: '600px', margin: '0 auto', padding: '0 16px' }}>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          style={{
            margin: '20px 0',
            padding: '12px 24px',
            fontSize: '16px',
            backgroundColor: '#1b74e4',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            width: '100%',
            maxWidth: '600px',
          }}
        >
          ➕ New Post
        </button>

        <CreatePostModal 
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onPostCreated={fetchPosts}
        />

        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>Loading feed...</div>
        ) : error ? (
          <div style={{ color: 'red', textAlign: 'center', padding: '20px' }}>{error}</div>
        ) : posts.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>No posts yet. Be the first to share something!</div>
        ) : (
          posts.map((post) => (
            <MatchPostContainer key={post.id}>
              {post.is_match_post && <LookalikesConnectedBanner />}
              <div style={{ padding: '16px' }}>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                  <MatchPostAvatar image={post.user?.profile_image_url || '/static/default_profile.png'} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                      <a href={post.profile_url} style={{ color: '#1b74e4', textDecoration: 'none' }}>
                        {post.username}
                      </a>
                    </div>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      {formatDate(post.created_at)}
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '12px', whiteSpace: 'pre-wrap' }}>
                  {post.content}
                </div>

                {post.face_filename && (
                  <div style={{ marginBottom: '12px' }}>
                    <MatchPostImageBorder image={`/static/extracted_faces/${post.face_filename}`} />
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <MatchPostLikeButton 
                    isLiked={post.user_has_liked}
                    onClick={() => handleLike(post.id)}
                  />
                  <MatchPostLikeCount text={`${post.likes_count} likes`} />
                </div>

                <MatchPostInputField 
                  onSubmit={(comment) => handleComment(post.id, comment)}
                  placeholder="Write a comment..."
                />
              </div>
            </MatchPostContainer>
          ))
        )}
      </div>
      <NavBar />
    </div>
  );
};

export default FeedPage;
