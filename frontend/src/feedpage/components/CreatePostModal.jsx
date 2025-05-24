import React, { useState } from 'react';
import MatchPostContainer from './matchpostcontainer';
import MatchPostAvatar from './matchpostavatar';
import MatchPostInputField from './matchpostInputField';

const CreatePostModal = ({ isOpen, onClose, onPostCreated }) => {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Please enter some content for your post');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('content', content);

      const response = await fetch('/social/feed/create_post', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to create post');
      }

      const data = await response.json();
      if (data.success) {
        setContent('');
        onPostCreated();
        onClose();
      } else {
        throw new Error(data.error || 'Failed to create post');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div className="modal-content" style={{
        width: '90%',
        maxWidth: '500px',
      }}>
        <MatchPostContainer>
          <div style={{ padding: '20px' }}>
            <button
              onClick={onClose}
              style={{
                position: 'absolute',
                right: '10px',
                top: '10px',
                background: 'none',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ✕
            </button>
            <h2 style={{ marginBottom: '20px', color: '#1b74e4' }}>Create New Post</h2>
            
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <MatchPostAvatar image="/static/default_profile.png" />
                <div style={{ flex: 1 }}>
                  <MatchPostInputField
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="What's on your mind?"
                    style={{
                      width: '100%',
                      minHeight: '150px',
                      marginBottom: '15px'
                    }}
                  />
                </div>
              </div>
              
              {error && (
                <div style={{ color: 'red', marginBottom: '15px', textAlign: 'center' }}>
                  {error}
                </div>
              )}
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={onClose}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: '1px solid #ddd',
                    backgroundColor: 'white',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    backgroundColor: '#1b74e4',
                    color: 'white',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer',
                    opacity: isSubmitting ? 0.7 : 1
                  }}
                >
                  {isSubmitting ? 'Posting...' : 'Post'}
                </button>
              </div>
            </form>
          </div>
        </MatchPostContainer>
      </div>
    </div>
  );
};

export default CreatePostModal; 