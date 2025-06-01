import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavBar from '../components/NavBar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBellSlash, faCheck, faUser, faHeart, faComment, faSearch, faPortrait, faShare } from '@fortawesome/free-solid-svg-icons';
import styles from './NotificationsPage.module.css';
import { API_BASE_URL } from '../config';

const NotificationsPage = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // Fetch notifications when component mounts
  useEffect(() => {
    fetchNotifications();
  }, []);

  // Function to fetch notifications from the API
  const fetchNotifications = async (pageNum = 1) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/social/notifications/?page=${pageNum}&per_page=10`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }
      
      const data = await response.json();
      
      if (pageNum === 1) {
        setNotifications(data.notifications);
      } else {
        setNotifications(prev => [...prev, ...data.notifications]);
      }
      
      setHasMore(data.has_more);
      setPage(pageNum);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Function to load more notifications
  const loadMore = () => {
    if (hasMore && !loading) {
      fetchNotifications(page + 1);
    }
  };

  // Function to mark a notification as read
  const markAsRead = async (notificationId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/social/notifications/${notificationId}/read`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to mark notification as read');
      }
      
      // Update the notification in the state
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Function to mark all notifications as read
  const markAllAsRead = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/social/notifications/mark_all_read`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to mark all notifications as read');
      }
      
      // Update all notifications in the state
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, is_read: true }))
      );
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Function to handle notification click
  const handleNotificationClick = (notification) => {
    // Mark the notification as read
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    
    // Navigate based on notification type and entity
    if (notification.entity_type === 'post' && notification.entity_id) {
      navigate(`/feed?post=${notification.entity_id}`);
    } else if (notification.entity_type === 'profile' && notification.entity_id) {
      navigate(`/profile/${notification.entity_id}`);
    } else if (notification.entity_type === 'match' && notification.entity_id) {
      navigate(`/matches?highlight=${notification.entity_id}`);
    } else {
      // Default to feed if no specific entity
      navigate('/feed');
    }
  };

  // Function to get icon for notification type
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'post_like':
        return <FontAwesomeIcon icon={faHeart} className={styles.likeIcon} />;
      case 'post_comment':
        return <FontAwesomeIcon icon={faComment} className={styles.commentIcon} />;
      case 'search_appearance':
        return <FontAwesomeIcon icon={faSearch} className={styles.searchIcon} />;
      case 'match_added_to_profile':
        return <FontAwesomeIcon icon={faPortrait} className={styles.matchIcon} />;
      case 'match_shared_to_feed':
        return <FontAwesomeIcon icon={faShare} className={styles.shareIcon} />;
      case 'new_follower':
        return <FontAwesomeIcon icon={faUser} className={styles.followerIcon} />;
      default:
        return <FontAwesomeIcon icon={faBellSlash} className={styles.defaultIcon} />;
    }
  };

  return (
    <div className={styles.notificationsPage}>
      <div className={styles.header}>
        <h1>Notifications</h1>
        {notifications.length > 0 && (
          <button className={styles.markAllReadBtn} onClick={markAllAsRead}>
            <FontAwesomeIcon icon={faCheck} /> Mark All Read
          </button>
        )}
      </div>
      
      <div className={styles.content}>
        {loading && page === 1 ? (
          <div className={styles.loading}>Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <FontAwesomeIcon icon={faBellSlash} size="3x" />
            </div>
            <h2>No Notifications</h2>
            <p>You don't have any notifications at the moment.</p>
          </div>
        ) : (
          <>
            <div className={styles.notificationsList}>
              {notifications.map(notification => (
                <div 
                  key={notification.id} 
                  className={`${styles.notificationItem} ${notification.is_read ? styles.read : styles.unread}`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className={styles.notificationIcon}>
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className={styles.notificationContent}>
                    <p className={styles.notificationText}>{notification.content}</p>
                    <p className={styles.notificationTime}>
                      {new Date(notification.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            {hasMore && (
              <div className={styles.loadMoreContainer}>
                <button 
                  className={styles.loadMoreBtn} 
                  onClick={loadMore}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
      
      {/* Navigation Bar */}
      <NavBar />
    </div>
  );
};

export default NotificationsPage;
