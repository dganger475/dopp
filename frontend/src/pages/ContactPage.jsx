import React from 'react';
import PageLayout from '../components/PageLayout';

const ContactPage = () => {
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
          📧 Contact Us
        </h1>
        <div style={{ 
          whiteSpace: 'pre-wrap', 
          lineHeight: 1.6,
          fontSize: '1rem',
          textAlign: 'center'
        }}>
          {`Doppleganger Social Network

📧 Email: dganger475@gmail.com

📍 Address: 2135 NW 13th St Unit 35, Gresham, OR 97030

We're here to help with:
• Questions about the app
• Privacy concerns
• Takedown requests
• Technical support
• General inquiries

We typically respond within 72 hours.

© 2025 Doppleganger Social Network. All rights reserved.`}
        </div>
      </div>
    </PageLayout>
  );
};

export default ContactPage; 