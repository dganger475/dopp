import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faSearch, faUser, faBell } from '@fortawesome/free-solid-svg-icons';

const NavBar = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path;
  };

  const iconStyle = {
    color: '#000',
    fontSize: '1.2rem'
  };

  const linkStyle = {
    textDecoration: 'none',
    color: '#000',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '8px 16px'
  };

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: '#fff',
      display: 'flex',
      justifyContent: 'space-around',
      padding: '8px 0',
      borderTop: '1px solid #eee',
      zIndex: 1000
    }}>
      <Link to="/social/feed" style={linkStyle}>
        <FontAwesomeIcon icon={faHome} style={iconStyle} />
        <span style={{ fontSize: '0.8rem', marginTop: '4px' }}>Home</span>
      </Link>
      <Link to="/search" style={linkStyle}>
        <FontAwesomeIcon icon={faSearch} style={iconStyle} />
        <span style={{ fontSize: '0.8rem', marginTop: '4px' }}>Search</span>
      </Link>
      <Link to="/profile/" style={linkStyle}>
        <FontAwesomeIcon icon={faUser} style={iconStyle} />
        <span style={{ fontSize: '0.8rem', marginTop: '4px' }}>Profile</span>
      </Link>
      <Link to="/notifications" style={linkStyle}>
        <FontAwesomeIcon icon={faBell} style={iconStyle} />
        <span style={{ fontSize: '0.8rem', marginTop: '4px' }}>Alerts</span>
      </Link>
    </nav>
  );
};

export default NavBar;
