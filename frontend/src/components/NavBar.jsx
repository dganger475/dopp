import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faSearch, faUser, faBell } from '@fortawesome/free-solid-svg-icons';
import API_BASE_URL from '../config/api';

const NavBar = () => {
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Fetch unread notification count when component mounts
  useEffect(() => {
    fetchUnreadCount();
    
    // Set up interval to periodically check for new notifications
    const interval = setInterval(fetchUnreadCount, 60000); // Check every minute
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);
  
  const fetchUnreadCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/social/notifications/unread_count`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.count);
      }
    } catch (error) {
      console.error('Error fetching unread notification count:', error);
    }
  };
  
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
    padding: '8px 16px',
    position: 'relative'
  };
  
  const badgeStyle = {
    position: 'absolute',
    top: '0',
    right: '8px',
    backgroundColor: '#ff4757',
    color: 'white',
    borderRadius: '50%',
    width: '18px',
    height: '18px',
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold'
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
        {unreadCount > 0 && (
          <span style={badgeStyle}>{unreadCount > 99 ? '99+' : unreadCount}</span>
        )}
        <span style={{ fontSize: '0.8rem', marginTop: '4px' }}>Alerts</span>
      </Link>
    </nav>
  );
};

export default NavBar;
