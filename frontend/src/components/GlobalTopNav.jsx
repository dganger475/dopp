import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faSearch, faUser, faBell } from '@fortawesome/free-solid-svg-icons';

const MOBILE_BREAKPOINT = 768; 
const logoUrl = "/static/images/logo.png"; // Path to logo in static/images directory

const GlobalTopNav = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const iconStyle = {
    color: '#000000', // Black color for icons
    fontSize: '24px', 
    textDecoration: 'none'
  };

  const navLinkStyle = {
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center'
  };
  
  return (
    <nav style={{
      width: '100%',
      height: '64px',
      background: 'var(--dopple-blue)',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 1000,
      borderBottom: '4px solid var(--dopple-black)'
    }}>
      {/* Logo positioned absolutely */}
      <div style={{ 
        position: 'absolute', 
        left: '20px', 
        top: '50%', 
        transform: 'translateY(-45%)' 
      }}>
        <Link to="/feed" style={{textDecoration: 'none', display: 'flex', alignItems: 'center'}}>
          <img src={logoUrl} alt="DoppleGanger Logo" style={{ height: 60, width: 60 }} />
        </Link>
      </div>
      
      {/* Icons positioned further right */}
      <div style={{ 
        position: 'absolute', 
        left: '62%', 
        top: '50%', 
        transform: 'translate(-50%, -50%)',
        display: 'flex',
        gap: isMobile ? '40px' : '65px'
      }}>
        <Link to="/feed" title="Feed" style={navLinkStyle}>
          <FontAwesomeIcon icon={faHome} style={iconStyle} />
        </Link>
        <Link to="/search" title="Search" style={navLinkStyle}>
          <FontAwesomeIcon icon={faSearch} style={iconStyle} />
        </Link>
        <Link to="/notifications" title="Notifications" style={navLinkStyle}>
          <FontAwesomeIcon icon={faBell} style={iconStyle} />
        </Link>
        <Link to="/profile/" title="Profile" style={navLinkStyle}>
          <FontAwesomeIcon icon={faUser} style={iconStyle} />
        </Link>
      </div>
    </nav>
  );
};

export default GlobalTopNav;
