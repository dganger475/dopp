import React, { useState } from "react";
import API_BASE_URL from '../config/api';
import { useNavigate, Link } from "react-router-dom";
import BlackHeader from "./black header.jsx";
import LoginHeaderLogo from "./login header logo.jsx";
import WelcomeBackText from "./welcome back text.jsx";
import InputField8 from "./login credentials/InputField (8).jsx";
import InputField9 from "./login credentials/InputField (9).jsx";
import Button8 from "./login credentials/Button (8).jsx";

// Global styles for Arial font
const globalStyle = document.createElement('style');
globalStyle.innerHTML = `
  * {
    font-family: Arial, sans-serif !important;
  }
`;
document.head.appendChild(globalStyle);

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      console.log('Login API response:', res);
      if (res.ok) {
        if (onLogin) {
          onLogin();
        }
        navigate("/social/feed");
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Login failed. Please try again.");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', padding: '2rem', background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <LoginHeaderLogo />
        <BlackHeader />
        <WelcomeBackText />
      </div>
      
      <form onSubmit={handleSubmit} style={{ margin: '2rem 0' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <InputField8
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <InputField9
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div style={{ marginTop: '1rem' }}>
          <Button8 />
        </div>
        {error && <div style={{ color: "#b00", marginTop: 10, textAlign: 'center' }}>{error}</div>}
        
        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '14px', color: '#666' }}>
          New here? <Link to="/register" style={{ color: '#646cff', textDecoration: 'none', fontWeight: 'bold' }}>Register</Link>
        </div>

        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '12px', color: '#666' }}>
          By continuing, you agree to our{' '}
          <Link to="/terms" style={{ color: '#646cff', textDecoration: 'none' }}>Terms & Conditions</Link>
          {' '}and{' '}
          <Link to="/privacy" style={{ color: '#646cff', textDecoration: 'none' }}>Privacy Policy</Link>
        </div>
      </form>
    </div>
  );
}

export default LoginPage;
