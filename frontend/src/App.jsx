import React, { useState, useEffect, Suspense } from 'react'; // Added Suspense
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'; // Added useLocation
import LoginPage from './loginpage/LoginPage'; 
import PlasmicHost from './plasmic-host';
import '../../static/css/main.css';
import GlobalTopNav from './components/GlobalTopNav'; // Import GlobalTopNav

// Lazy load page components for better initial load time
const SearchPage = React.lazy(() => import('./searchPage/SearchPage'));
const ProfilePage = React.lazy(() => import('./ProfilePage'));
const EditProfilePage = React.lazy(() => import('./profilepage/EditProfilePage'));
const FeedPage = React.lazy(() => import('./feedpage/FeedPage'));
const RegisterPage = React.lazy(() => import('./registrationpage/RegistrationPage'));
const WelcomePage = React.lazy(() => import('./welcomepage/WelcomePage')); // Path to be confirmed

const AppContent = () => {
  const location = useLocation();
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('/auth/current_user', { 
          credentials: 'include',
          headers: { 'Cache-Control': 'no-cache' }
        });
        setLoggedIn(response.ok);
      } catch (error) {
        console.error('Authentication check failed:', error);
        setLoggedIn(false);
      } finally {
        setLoading(false);
      }
    };
    checkAuthStatus();
  }, []);

  const noNavPaths = ['/login', '/register', '/welcome', '/plasmic-host'];
  const showNav = !noNavPaths.some(path => location.pathname.startsWith(path));

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
            <Route path="/" element={loggedIn ? <Navigate to="/social/feed" replace /> : <Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage onLogin={() => setLoggedIn(true)} />} />
            <Route path="/register" element={<RegisterPage />} /> 
            <Route path="/welcome" element={<WelcomePage />} />

            <Route path="/search" element={loggedIn ? <SearchPage /> : <Navigate to="/login" replace />} />
            <Route path="/profile/" element={loggedIn ? <Suspense fallback={<div>Loading...</div>}><ProfilePage /></Suspense> : <Navigate to="/login" replace />} />
            <Route path="/edit-profile" element={loggedIn ? <EditProfilePage /> : <Navigate to="/login" replace />} />
            <Route path="/social/feed" element={loggedIn ? <FeedPage /> : <Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </div>
    </>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
