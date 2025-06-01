import React, { useState } from 'react';

const MatchPostInputField = ({ onSubmit, placeholder, style = {} }) => {
  const [comment, setComment] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (comment.trim()) {
      onSubmit(comment);
      setComment('');
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        gap: '8px',
        ...style
      }}
    >
      <input
        type="text"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder={placeholder}
        style={{
          flex: 1,
          backgroundColor: '#ffffff',
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          padding: '4px 8px',
          fontSize: '12px',
          color: '#000000',
          outline: 'none',
          ...(style['& input'] || {})
        }}
      />
      <button
        type="submit"
        disabled={!comment.trim()}
        style={{
          backgroundColor: '#000000',
          color: '#ffffff',
          border: 'none',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          cursor: comment.trim() ? 'pointer' : 'not-allowed',
          opacity: comment.trim() ? 1 : 0.5,
          transition: 'opacity 0.2s',
          ...(style['& button'] || {})
        }}
      >
        Post
      </button>
    </form>
  );
};

export default MatchPostInputField;