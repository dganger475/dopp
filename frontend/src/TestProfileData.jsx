import React, { useState, useEffect } from 'react';
import API_BASE_URL from './config/api';

const TestProfileData = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        console.log('Fetching user data from:', `${API_BASE_URL}/api/users/current`);
        const response = await fetch(`${API_BASE_URL}/api/users/current`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });

        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received user data:', data);
        setUserData(data);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  if (loading) return <div>Loading user data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!userData) return <div>No user data available</div>;

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>User Data Test</h1>
      <h2>Raw Response:</h2>
      <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '5px', overflow: 'auto', maxHeight: '400px' }}>
        {JSON.stringify(userData, null, 2)}
      </pre>
      
      <h2>User Object:</h2>
      {userData.user ? (
        <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '5px', overflow: 'auto', maxHeight: '400px' }}>
          {JSON.stringify(userData.user, null, 2)}
        </pre>
      ) : (
        <p>No user object found in response</p>
      )}
      
      <h2>Important Fields:</h2>
      <ul style={{ background: '#f5f5f5', padding: '20px', borderRadius: '5px' }}>
        <li><strong>Bio:</strong> {userData.user?.bio || (userData.bio || 'Not available')}</li>
        <li><strong>Current City:</strong> {userData.user?.current_city || userData.user?.current_location_city || (userData.current_city || 'Not available')}</li>
        <li><strong>Member Since:</strong> {userData.user?.memberSince || userData.user?.created_at || (userData.memberSince || 'Not available')}</li>
      </ul>
    </div>
  );
};

export default TestProfileData;
