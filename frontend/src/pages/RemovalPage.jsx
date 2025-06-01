import React, { useState } from 'react';
import PageLayout from '../components/PageLayout';

const RemovalPage = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Here you would typically send the request to your backend
    // For now, we'll just show a success message
    setSubmitted(true);
  };

  return (
    <PageLayout>
      <div style={{ 
        maxWidth: 800, 
        margin: '2rem auto', 
        padding: '2rem', 
        background: '#fff', 
        borderRadius: 12, 
        boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
        color: '#333'
      }}>
        <h1 style={{ 
          fontSize: '2rem', 
          marginBottom: '1.5rem', 
          color: '#1b74e4',
          textAlign: 'center'
        }}>
          Request Content Removal
        </h1>

        {!submitted ? (
          <div>
            <p style={{ marginBottom: '1.5rem', lineHeight: 1.6 }}>
              If you've found your image on Doppleganger.us and would like it removed, please fill out the form below. 
              We'll review your request and remove the content within 72 hours.
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label htmlFor="email" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Your Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem'
                  }}
                />
              </div>

              <div>
                <label htmlFor="message" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Additional Information
                </label>
                <textarea
                  id="message"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  required
                  placeholder="Please provide any additional details that will help us locate and remove your content..."
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem',
                    minHeight: '150px',
                    resize: 'vertical'
                  }}
                />
              </div>

              <button
                type="submit"
                style={{
                  background: '#1b74e4',
                  color: 'white',
                  border: 'none',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  fontWeight: 500,
                  marginTop: '1rem'
                }}
              >
                Submit Removal Request
              </button>
            </form>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <h2 style={{ color: '#1b74e4', marginBottom: '1rem' }}>Request Submitted</h2>
            <p style={{ lineHeight: 1.6 }}>
              Thank you for your request. We'll review it and process the removal within 72 hours.
              You'll receive a confirmation email at {email} once the content has been removed.
            </p>
          </div>
        )}
      </div>
    </PageLayout>
  );
};

export default RemovalPage; 