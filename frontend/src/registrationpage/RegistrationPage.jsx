import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config/api';
import BlackHeader from '../loginpage/black header.jsx';
import LoginHeaderLogo from '../loginpage/login header logo.jsx';

// Global styles for Arial font
const globalStyle = document.createElement('style');
globalStyle.innerHTML = `
  * {
    font-family: Arial, sans-serif !important;
  }
`;
document.head.appendChild(globalStyle);

const RegistrationPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [headshot, setHeadshot] = useState(null);
  const [headshotPreview, setHeadshotPreview] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleHeadshotChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setHeadshot(file);
      setHeadshotPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    // Validate passwords match
    if (password !== password2) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    
    // Validate headshot is provided
    if (!headshot) {
      setError('Please upload a headshot image');
      setLoading(false);
      return;
    }
    
    try {
      // Create FormData to handle file upload
      const formData = new FormData();
      formData.append('username', username);
      formData.append('email', email);
      formData.append('password', password);
      formData.append('password2', password2);
      formData.append('profile_photo', headshot);
      
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      
      let data = {};
      try {
        data = await res.json();
      } catch (e) {
        data = { error: 'Unexpected server response. Please try again.' };
      }
      
      if (res.ok) {
        // Registration successful
        navigate('/instructions');
      } else {
        setError(data.error || 'Registration failed. Please try again.');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', padding: '2rem', background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <LoginHeaderLogo />
        <BlackHeader />
        <div style={{ color: '#1c1e21', fontSize: '24px', fontFamily: 'Arial, sans-serif', fontWeight: 300, lineHeight: '32px', textAlign: 'center', marginTop: '1rem' }}>
          Create Your Account
        </div>
      </div>
      
      <form onSubmit={handleSubmit} style={{ margin: '2rem 0' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            style={{
              width: '100%',
              height: '44px',
              padding: '0px 12px',
              border: '1px solid #ddd',
              boxSizing: 'border-box',
              borderRadius: '6px',
              backgroundColor: '#f5f5f5',
              color: '#333',
              fontSize: '14px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 400,
              lineHeight: '44px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            required
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            style={{
              width: '100%',
              height: '44px',
              padding: '0px 12px',
              border: '1px solid #ddd',
              boxSizing: 'border-box',
              borderRadius: '6px',
              backgroundColor: '#f5f5f5',
              color: '#333',
              fontSize: '14px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 400,
              lineHeight: '44px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            required
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            style={{
              width: '100%',
              height: '44px',
              padding: '0px 12px',
              border: '1px solid #ddd',
              boxSizing: 'border-box',
              borderRadius: '6px',
              backgroundColor: '#f5f5f5',
              color: '#333',
              fontSize: '14px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 400,
              lineHeight: '44px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            required
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <input
            type="password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            placeholder="Confirm Password"
            style={{
              width: '100%',
              height: '44px',
              padding: '0px 12px',
              border: '1px solid #ddd',
              boxSizing: 'border-box',
              borderRadius: '6px',
              backgroundColor: '#f5f5f5',
              color: '#333',
              fontSize: '14px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 400,
              lineHeight: '44px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            required
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            Upload Headshot (Required)
          </div>
          <input
            type="file"
            accept="image/*"
            onChange={handleHeadshotChange}
            style={{
              width: '100%',
              padding: '8px 0',
            }}
            required
          />
          {headshotPreview && (
            <div style={{ marginTop: '12px', textAlign: 'center' }}>
              <img 
                src={headshotPreview} 
                alt="Headshot Preview" 
                style={{
                  width: '120px',
                  height: '120px',
                  objectFit: 'cover',
                  borderRadius: '50%',
                  border: '2px solid #ddd'
                }}
              />
            </div>
          )}
        </div>
        <div style={{ marginTop: '1rem' }}>
          <button 
            type="submit" 
            disabled={loading}
            style={{
              cursor: loading ? 'not-allowed' : 'pointer',
              width: '100%',
              height: '44px',
              padding: '0px 16px',
              border: '0',
              boxSizing: 'border-box',
              borderRadius: '6px',
              backgroundColor: loading ? '#a8aaff' : '#646cff',
              color: '#fff',
              fontSize: '16px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 700,
              lineHeight: '44px',
              outline: 'none',
              transition: 'background-color 0.2s ease',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            {loading ? 'Processing...' : 'Register'}
          </button>
        </div>
        {error && <div style={{ color: "#b00", marginTop: 10, textAlign: 'center' }}>{error}</div>}
        
        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '14px', color: '#666' }}>
          Already have an account? <Link to="/login" style={{ color: '#646cff', textDecoration: 'none', fontWeight: 'bold' }}>Login</Link>
        </div>

        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '12px', color: '#666' }}>
          By registering, you agree to our{' '}
          <Link to="/terms" style={{ color: '#646cff', textDecoration: 'none' }}>Terms & Conditions</Link>
          {' '}and{' '}
          <Link to="/privacy" style={{ color: '#646cff', textDecoration: 'none' }}>Privacy Policy</Link>
        </div>
      </form>
    </div>
  );
};

export default RegistrationPage;