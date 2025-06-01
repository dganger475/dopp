import React from 'react';
import PropTypes from 'prop-types';
import { getFaceImageUrl, getProfileImageUrl } from '../utils/imageUrls';

/**
 * FaceMatch component for displaying a face match comparison.
 */
const FaceMatch = ({ 
  userImageUrl, 
  faceFilename, 
  username, 
  similarity, 
  state, 
  decade 
}) => {
  return (
    <div className="match-comparison" style={{
      display: 'flex',
      justifyContent: 'space-between',
      margin: '8px 0'
    }}>
      {/* User's face */}
      <div className="face" style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '48%'
      }}>
        <div className="avatar" style={{
          width: '100px',
          height: '100px',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <img 
            src={getProfileImageUrl(userImageUrl)} 
            alt="User avatar" 
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              borderRadius: '4px'
            }}
          />
        </div>
        <div className="label" style={{
          background: 'var(--primary)',
          color: '#fff',
          borderRadius: '6px',
          padding: '2px 10px',
          marginTop: '4px',
          fontWeight: '600',
          fontSize: '12px',
          display: 'inline-block'
        }}>
          {username}
        </div>
      </div>

      {/* Matched face */}
      <div className="face" style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '48%'
      }}>
        <img 
          src={getFaceImageUrl(faceFilename)} 
          alt="Match" 
          style={{
            width: '100px',
            height: '100px',
            objectFit: 'cover',
            borderRadius: '4px'
          }}
        />
        <div className="label" style={{
          background: 'var(--primary)',
          color: '#fff',
          borderRadius: '6px',
          padding: '2px 10px',
          marginTop: '4px',
          fontWeight: '600',
          fontSize: '12px',
          display: 'inline-block'
        }}>
          Match
        </div>
      </div>

      {/* Match metadata */}
      <div className="match-meta" style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        margin: '6px 0',
        fontSize: '12px'
      }}>
        {similarity && (
          <div className="meta-item" style={{
            background: '#f0f0f0',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            Similarity: <b>{similarity}%</b>
          </div>
        )}
        {state && (
          <div className="meta-item" style={{
            background: '#f0f0f0',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            State: {state}
          </div>
        )}
        {decade && (
          <div className="meta-item" style={{
            background: '#f0f0f0',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            Decade: {decade}
          </div>
        )}
      </div>
    </div>
  );
};

FaceMatch.propTypes = {
  userImageUrl: PropTypes.string,
  faceFilename: PropTypes.string.isRequired,
  username: PropTypes.string.isRequired,
  similarity: PropTypes.number,
  state: PropTypes.string,
  decade: PropTypes.string
};

export default FaceMatch; 