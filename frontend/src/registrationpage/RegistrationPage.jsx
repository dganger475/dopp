import React, { useState } from 'react';
import UniversalCard from '../components/UniversalCard';
// Import your provided header, logo, and icons here

const RegistrationPage = () => {
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    faceImage: null,
    faceImageUrl: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (files) {
      const file = files[0];
      setForm((prev) => ({
        ...prev,
        faceImage: file,
        faceImageUrl: URL.createObjectURL(file),
      }));
    } else {
      setForm((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    const data = new FormData();
    data.append('name', form.name);
    data.append('email', form.email);
    data.append('password', form.password);
    data.append('face_image', form.faceImage);

    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        body: data,
      });
      const result = await res.json();
      if (result.success) {
        setSuccess('Registration successful! You can now log in.');
      } else {
        setError(result.error || 'Registration failed.');
      }
    } catch (err) {
      setError('Registration failed. Please try again.');
    }
  };

  return (
    <div style={{ background: '#fff', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Custom Header, Logo, and Icons go here */}
      <div style={{ width: 375, margin: '40px auto 0 auto', background: '#f7f7f7', borderRadius: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', padding: 24 }}>
        <h2 style={{ color: '#1b74e4', textAlign: 'center', marginBottom: 24 }}>Create Your Account</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label>Name</label>
            <input name="name" type="text" value={form.name} onChange={handleChange} required style={{ width: '100%', borderRadius: 6, border: '1px solid #e4e6eb', padding: 8 }} />
          </div>
          <div>
            <label>Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required style={{ width: '100%', borderRadius: 6, border: '1px solid #e4e6eb', padding: 8 }} />
          </div>
          <div>
            <label>Password</label>
            <input name="password" type="password" value={form.password} onChange={handleChange} required style={{ width: '100%', borderRadius: 6, border: '1px solid #e4e6eb', padding: 8 }} />
          </div>
          <div>
            <label>Upload Face Image</label>
            <input name="faceImage" type="file" accept="image/*" onChange={handleChange} required style={{ width: '100%', borderRadius: 6, border: '1px solid #e4e6eb', padding: 8 }} />
          </div>
          <button type="submit" style={{ background: '#1b74e4', color: '#fff', border: 'none', borderRadius: 6, padding: 12, fontWeight: 700 }}>Sign Up</button>
          {error && <div style={{ color: 'red', textAlign: 'center' }}>{error}</div>}
          {success && <div style={{ color: 'green', textAlign: 'center' }}>{success}</div>}
        </form>
        {/* Live preview of the user card */}
        <div style={{ marginTop: 32, display: 'flex', justifyContent: 'center' }}>
          <UniversalCard
            image={form.faceImageUrl || '/static/images/default_profile.png'}
            username={form.name || 'Username'}
            label={form.email ? 'REGISTERED USER' : 'UNCLAIMED PROFILE'}
            labelColor={form.email ? '#fff' : '#fff'}
            labelBg={form.email ? '#0075ff' : '#000'}
            decade={''}
            state={''}
            similarity={null}
            isRegistered={!!form.email}
          />
        </div>
      </div>
    </div>
  );
};

export default RegistrationPage; 