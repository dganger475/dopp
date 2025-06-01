import React from 'react';
import PageLayout from '../components/PageLayout';

const AboutPage = () => {
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
          👥 About Doppleganger Social Network
        </h1>
        <div style={{ 
          whiteSpace: 'pre-wrap', 
          lineHeight: 1.6,
          fontSize: '1rem'
        }}>
          {`Find Your Face in History. Discover Your Look-Alikes.

Doppleganger Social Network is a unique face-matching app that lets you explore visual similarities between your face and tens of thousands of anonymized faces extracted from public yearbooks. Whether you're curious about your historical twin or just want to see who you resemble, this app makes it fun, private, and surprisingly personal.

🔍 How It Works
Upload a Selfie – Start by submitting a photo of your face.

Get Instant Matches – We compare it against a massive database of faces using advanced facial recognition.

Explore Your Matches – View your closest visual matches from old yearbooks and other users.

Join the Network – Your uploaded face becomes searchable, allowing others to match with you in future results.

🛡️ Privacy First
All yearbook images in our database were gathered from publicly available sources and have been anonymized by removing school names, years, and locations.

Only registered users can recognize themselves.

We do not identify or label anyone.

If you appear in the database and want your photo removed, email us and we'll take care of it quickly.

📧 dganger475@gmail.com

🤝 Our Mission
Doppleganger Social Network is more than a novelty—it's a bridge across time and identity. We aim to:

Give people a fun, reflective experience with their appearance and heritage.

Build a community that's curious, respectful, and visually connected.

Explore how facial features connect us across generations and geography.

👤 Created By
Jacob Layton
Developer & Founder
© 2025 Doppleganger Social Network. All rights reserved.`}
        </div>
      </div>
    </PageLayout>
  );
};

export default AboutPage; 