import React, { useState } from 'react';

const styles = {
  Container: {
    display: 'flex',
    gap: '8px',
    marginTop: '10px',
  },
  Input: {
    flex: 1,
    height: '40px',
    padding: '0 12px',
    border: '2px solid #030303',
    boxSizing: 'border-box',
    borderRadius: '6px',
    backgroundColor: '#e4e6eb',
    color: '#050505',
    fontSize: '14px',
    fontFamily: 'Source Sans Pro',
    fontWeight: 700,
    outline: 'none',
  },
  Button: {
    height: '40px',
    padding: '0 16px',
    border: '2px solid #030303',
    borderRadius: '6px',
    backgroundColor: '#1b74e4',
    color: '#ffffff',
    fontSize: '14px',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'opacity 0.2s ease',
  },
  ButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  }
};

const MatchPostInputField = ({ onSubmit, placeholder = 'Write a comment...' }) => {
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!comment.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onSubmit(comment);
      setComment('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={styles.Container}>
      <input
        style={styles.Input}
        placeholder={placeholder}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={isSubmitting}
      />
      <button
        style={{
          ...styles.Button,
          ...(isSubmitting || !comment.trim() ? styles.ButtonDisabled : {})
        }}
        onClick={handleSubmit}
        disabled={isSubmitting || !comment.trim()}
      >
        {isSubmitting ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
};

export default MatchPostInputField;