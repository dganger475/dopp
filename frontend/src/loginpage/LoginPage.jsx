import React, { useState } from "react";
import API_BASE_URL from '../config/api';
import { useNavigate } from "react-router-dom";
import BlackHeader from "./black header.jsx";
import LoginHeaderLogo from "./login header logo.jsx";
import WelcomeBackText from "./welcome back text.jsx";
import InputField8 from "./login credentials/InputField (8).jsx";
import InputField9 from "./login credentials/InputField (9).jsx";
import Button8 from "./login credentials/Button (8).jsx";
import ContinueWithEmail from "./Continue with Email button.jsx";
import ContinueWithGoogle from "./Continue with Google button.jsx";
import ContinueWithFacebook from "./Continue with FacebookButton (8).jsx";
import CreateNewAccountText from "./create new account text.jsx";

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
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
        body: JSON.stringify({ email, password })
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
      <BlackHeader />
      <LoginHeaderLogo />
      <WelcomeBackText />
      <form onSubmit={handleSubmit} style={{ margin: '2rem 0' }}>
        <InputField8
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <InputField9
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button8 />
        {error && <div style={{ color: "#b00", marginTop: 10 }}>{error}</div>}
      </form>
      <ContinueWithEmail />
      <ContinueWithGoogle />
      <ContinueWithFacebook />
      <div style={{ marginTop: '2rem' }}>
        <CreateNewAccountText />
      </div>
    </div>
  );
}

export default LoginPage;
