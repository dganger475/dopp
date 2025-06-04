import React, { useState, useEffect, Suspense } from 'react'; // Added Suspense
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'; // Added useLocation
import LoginPage from './loginpage/LoginPage'; 
import PlasmicHost from './plasmic-host';
import './App.css';
import GlobalTopNav from './components/GlobalTopNav'; // Import GlobalTopNav
import { SharedMatchProvider } from './context/SharedMatchContext'; // Import SharedMatchProvider
import API_BASE_URL from './config/api';
import PageLayout from './components/PageLayout';
import ErrorBoundary from './components/ErrorBoundary';

// Loading fallback component
const LoadingFallback = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh',
    background: '#f5f5f5'
  }}>
    <div style={{ 
      textAlign: 'center',
      padding: '2rem',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <div style={{ 
        width: '40px', 
        height: '40px', 
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 1rem'
      }} />
      <p>Loading...</p>
    </div>
  </div>
);

// Lazy load page components with loading fallback
const lazyLoad = (importFunc) => {
  const Component = React.lazy(importFunc);
  return (props) => (
    <Suspense fallback={<LoadingFallback />}>
      <Component {...props} />
    </Suspense>
  );
};

// Lazy load page components
const SearchPage = lazyLoad(() => import('./searchPage/SearchPage'));
const ProfilePage = lazyLoad(() => import('./ProfilePage'));
const EditProfilePage = lazyLoad(() => import('./edit_profile_new/EditProfilePage'));
const TestProfileData = lazyLoad(() => import('./TestProfileData'));
const FeedPage = lazyLoad(() => import('./feedpage/FeedPage'));
const RegisterPage = lazyLoad(() => import('./registrationpage/RegistrationPage'));
const WelcomePage = lazyLoad(() => import('./welcomepage/WelcomePage')); // Path to be confirmed
const NotificationsPage = lazyLoad(() => import('./notificationspage/NotificationsPage'));
const ComparisonPage = lazyLoad(() => import('./comparisonpage/ComparisonPage'));
const InstructionsPage = lazyLoad(() => import('./instructionspage/InstructionsPage'));
const TermsPage = lazyLoad(() => import('./pages/TermsPage'));
const PrivacyPage = lazyLoad(() => import('./pages/PrivacyPage'));
const AboutPage = lazyLoad(() => import('./pages/AboutPage'));
const ContactPage = lazyLoad(() => import('./pages/ContactPage'));
const RemovalPage = lazyLoad(() => import('./pages/RemovalPage'));

// Terms and Privacy Policy components
const TermsPageContent = () => (
  <div style={{ maxWidth: 800, margin: '2rem auto', padding: '2rem', background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}>
    <h1>Terms and Conditions</h1>
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
      {`Terms and Conditions for Doppleganger Social Network
Effective Date: May 30, 2025

Welcome to Doppleganger Social Network (the "App" or "Service"), developed and operated by Jacob Layton ("Developer", "we", "us", or "our").

By accessing or using the App, you agree to be bound by the following Terms and Conditions. If you do not agree with any part of these terms, you must not use the App.

1. Purpose of the App
The Doppleganger App allows users to explore visual matches from a database of publicly sourced yearbook images. These images are used to create AI-powered face-matching experiences.

2. Data and Image Sources
All images and data in this App originate from publicly available yearbooks, primarily sourced from public archives. These yearbooks are understood to be in the public domain or publicly accessible under U.S. law.
To protect individual privacy:

The exact school name, location, and year of each yearbook image has been redacted or censored.

Only facial images are retained for the purposes of face matching.

If you believe your image has been used and wish to have it removed, please contact us at dganger475@gmail.com with your request, and we will process removal as soon as reasonably possible.

3. Your Responsibilities
By using the App, you agree:

Not to misuse, redistribute, or attempt to de-anonymize the data presented in the App.

Not to attempt to identify or dox other users or image subjects.

Not to upload unlawful, explicit, or harmful content.

4. Intellectual Property
All content, features, and functionality of the App, including but not limited to software, text, images, logos, and trademarks, are the intellectual property of Jacob Layton unless otherwise noted.
Unauthorized reproduction, redistribution, or exploitation of any part of the App is strictly prohibited.

5. No Guarantee of Accuracy
While we strive to offer an entertaining and informative experience, all matches and face similarity results are generated by machine learning algorithms and may not be factually accurate or verifiable.

We do not guarantee the identity, resemblance, or relationship between any person and a matched image.

6. User-Generated Content
If you choose to upload your own images or content:

You retain ownership of your content.

You grant us a non-exclusive, royalty-free license to process, analyze, and store that content for face-matching functionality.

You are solely responsible for any content you upload and represent that you have the legal right to share it.

7. DMCA and Takedown Policy
We comply with the Digital Millennium Copyright Act (DMCA).
If you believe that content on the App infringes upon your copyright or privacy rights, please send a detailed request to:

Email: dganger475@gmail.com
Address: 2135 NW 13th St Unit 35, Gresham, OR 97030

We reserve the right to take down any content that violates legal rights or community standards.

8. Limitation of Liability
To the maximum extent permitted by applicable law, the Developer shall not be liable for any:

Indirect, incidental, special, punitive, or consequential damages,

Loss of data, profits, reputation, or business interruption,

Claims related to likeness, identity, or accuracy of image matches.

Use of the App is at your own risk, and you accept the functionality "as-is."

9. Privacy and Data Use
We do not collect or store personally identifiable information unless voluntarily submitted by the user. All usage data is anonymized.
Our privacy practices are governed by our Privacy Policy.

10. Changes to These Terms
We reserve the right to modify these Terms at any time. When changes are made, we will update the effective date. Your continued use of the App signifies your acceptance of the revised terms.

11. Governing Law
These Terms are governed by and construed in accordance with the laws of the State of Oregon, United States.

Contact Information

Doppleganger Social Network
Jacob Layton (Developer)
📧 Email: dganger475@gmail.com
📍 Address: 2135 NW 13th St Unit 35, Gresham, OR 97030
© 2025 All Rights Reserved`}
    </div>
  </div>
);

const PrivacyPageContent = () => (
  <div style={{ maxWidth: 800, margin: '2rem auto', padding: '2rem', background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}>
    <h1>Privacy Policy</h1>
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
      {`Privacy Policy for Doppleganger Social Network
Effective Date: May 30, 2025

This Privacy Policy describes how Doppleganger Social Network ("we", "us", "our", or "the App") collects, uses, and protects your information. By using the App, you agree to the terms outlined here.

1. Who We Are
The App is developed and maintained by:

Jacob Layton
📧 Email: dganger475@gmail.com
📍 Address: 2135 NW 13th St Unit 35, Gresham, OR 97030

2. Information We Collect
We collect the following types of information from users:

a. User-Provided Information
Name (First and/or Last Name)

Uploaded Images (used for face matching)

Optional metadata: age, decade, gender, state, and other demographic tags

Contact information if provided in communications (e.g., email)

b. Automatically Collected Information
Device type and technical logs

Anonymous analytics (e.g., page visits, feature usage)

We do not collect payment information or precise GPS location data.

3. How We Use Your Information
We use the information collected to:

Match your uploaded images against our public yearbook face database

Display visual similarity results and match history

Personalize your experience and improve app features

Respond to support or image removal requests

Maintain app security and performance

4. Source of Our Dataset
All preloaded images used in the App come from publicly available yearbooks, sourced from open internet archives. We have:

Censored identifying yearbook data including school names, locations, and years to protect privacy

Removed all metadata that could be used to trace identities or locations

If your face appears in the app and you would like it removed, please contact us, and we will act quickly.

5. User Content and Responsibility
When you upload a photo or provide your name or demographic tags, you affirm that:

You have the right to use and share that content

You understand this information will be used for face matching

You are not uploading unlawful, harmful, or misleading content

6. Image and Face Data Handling
Uploaded images are used to generate face embeddings (numerical data used for matching)

These embeddings are stored for the purpose of enabling visual similarity searches

We do not share or sell your uploaded photos, embeddings, or names with third parties

7. Data Retention and Removal
You may request deletion of your name, photo, and associated face data at any time by contacting:

📧 dganger475@gmail.com

We will respond promptly and ensure removal of your data from our systems, typically within 72 hours.

8. Your Rights
You have the right to:

Request access to your stored data

Correct or update personal information

Request deletion of your photo, name, or any data you've submitted

Object to certain data processing practices

9. Security Measures
We take the following steps to protect your data:

Secure storage of uploaded photos and embeddings

Limited internal access to user data

Regular monitoring of systems for vulnerabilities

However, no system is 100% secure, and by using the App, you accept this inherent risk.

10. Children's Privacy
This App is not intended for children under 13. We do not knowingly collect data from minors.
Images from yearbooks are filtered to favor sources with adult subjects (18+), though complete verification is not guaranteed.

11. Policy Changes
We may update this Privacy Policy occasionally. The most current version will always be available in the app or linked documentation. Continued use of the app after changes means you accept the updated terms.

12. Contact Us
For questions, concerns, or takedown requests, contact:
Jacob Layton
📧 dganger475@gmail.com
📍 2135 NW 13th St Unit 35, Gresham, OR 97030

© 2025 Doppleganger Social Network. All rights reserved.`}
    </div>
  </div>
);

const AppContent = () => {
  const location = useLocation();
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Use the correct API_BASE_URL from config
        const response = await fetch(`${API_BASE_URL}/auth_status`, { 
          method: 'GET',
          credentials: 'include',
          headers: { 
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          },
          mode: 'cors'
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Authentication successful:', data);
          setLoggedIn(data.authenticated);
        } else {
          console.warn('Authentication failed with status:', response.status);
          setLoggedIn(false);
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        setLoggedIn(false);
      } finally {
        setLoading(false);
      }
    };
    checkAuthStatus();
  }, []); // Only run once on mount

  const noNavPaths = ['/login', '/register', '/welcome', '/plasmic-host', '/terms', '/privacy']; // Added terms and privacy paths
  const showNav = !noNavPaths.some(path => location.pathname.startsWith(path));

  // Check if current page should use PageLayout
  const shouldUseLayout = () => {
    const path = location.pathname;
    return !['/welcome', '/register', '/instructions'].includes(path);
  };

  // Wrap component with PageLayout if needed
  const wrapWithLayout = (Component) => {
    if (shouldUseLayout()) {
      return (
        <PageLayout>
          <Component />
        </PageLayout>
      );
    }
    return <Component />;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        Loading...
      </div>
    );
  }

  return (
    <>
      {showNav && <GlobalTopNav />}
      <div style={{ paddingTop: showNav ? '68px' : '0' }}>
        <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 68px)' }}>Loading Page...</div>}>
          <Routes>
            <Route path="/plasmic-host" element={<PlasmicHost />} />
            <Route path="/" element={<WelcomePage />} />
            <Route path="/login" element={<LoginPage onLogin={() => window.location.href = '/instructions'} />} />
            <Route path="/register" element={<RegisterPage />} /> 
            <Route path="/welcome" element={<WelcomePage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/removal" element={<RemovalPage />} />
            <Route path="/instructions" element={loggedIn ? <InstructionsPage onContinue={() => window.location.href = '/feed'} /> : <Navigate to="/login" replace />} />
            <Route path="/search" element={wrapWithLayout(SearchPage)} />
            <Route path="/profile" element={wrapWithLayout(ProfilePage)} />
            <Route path="/edit-profile" element={wrapWithLayout(EditProfilePage)} />
            <Route path="/test-profile" element={wrapWithLayout(TestProfileData)} />
            <Route path="/feed" element={wrapWithLayout(FeedPage)} />
            <Route path="/notifications" element={wrapWithLayout(NotificationsPage)} />
            <Route path="/comparison/:matchId" element={wrapWithLayout(ComparisonPage)} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </div>
    </>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <SharedMatchProvider>
          <AppContent />
        </SharedMatchProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
