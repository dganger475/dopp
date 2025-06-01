import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './EditProfilePage.module.css';
import API_BASE_URL from '../config/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faPlus } from '@fortawesome/free-solid-svg-icons';

const EditProfilePage = () => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    hometown: '',
    current_location_city: '',
    bio: ''
  });
  const [profileImage, setProfileImage] = useState(null);
  const [profileImagePreview, setProfileImagePreview] = useState(null);
  const [coverPhoto, setCoverPhoto] = useState(null);
  const [coverPhotoPreview, setCoverPhotoPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Fetch user data when component mounts
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
        
        if (data.success) {
          setUserData(data);
          setFormData({
            username: data.user.username || '',
            hometown: data.user.hometown || '',
            current_location_city: data.user.current_location_city || '',
            bio: data.user.bio || ''
          });
          
          // Set profile image preview if it exists
          if (data.user.profile_image_url) {
            setProfileImagePreview(
              data.user.profile_image_url.startsWith('http') 
                ? data.user.profile_image_url 
                : `${API_BASE_URL}${data.user.profile_image_url}`
            );
          }
          
          // Set cover photo preview if it exists
          if (data.user.cover_photo_url) {
            setCoverPhotoPreview(
              data.user.cover_photo_url.startsWith('http') 
                ? data.user.cover_photo_url 
                : `${API_BASE_URL}${data.user.cover_photo_url}`
            );
          }
        } else {
          throw new Error(data.message || 'Failed to fetch user data');
        }
      } catch (err) {
        console.error('Error fetching user data:', err);
        // Try to get more information about the error
        if (err.name === 'TypeError' && err.message.includes('Failed to fetch')) {
          setError('Network error: Could not connect to the server. This might be due to CORS issues.');
          console.error('This is likely a CORS issue. Check that the server is setting the correct CORS headers.');
        } else {
          setError(`${err.name}: ${err.message}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleProfileImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProfileImage(file);
      setProfileImagePreview(URL.createObjectURL(file));
    }
  };

  const handleCoverPhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCoverPhoto(file);
      setCoverPhotoPreview(URL.createObjectURL(file));
    }
  };

  const [successMessage, setSuccessMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    setSuccessMessage(null);

    try {
      const userId = userData.user.id;
      if (!userId) {
        throw new Error('User ID not found');
      }
      
      const formDataObj = new FormData();
      
      // Add text fields with detailed logging
      Object.keys(formData).forEach(key => {
        console.log(`Adding form field: ${key} = ${formData[key]}`);
        formDataObj.append(key, formData[key]);
      });
      
      // Add files if they exist
      if (profileImage) {
        console.log('Adding profile image to form data');
        formDataObj.append('profile_image', profileImage);
      }
      
      if (coverPhoto) {
        console.log('Adding cover photo to form data');
        formDataObj.append('cover_photo', coverPhoto);
      }
      
      console.log(`Submitting profile update to: ${API_BASE_URL}/profile/update/${userId}`);
      
      const response = await fetch(`${API_BASE_URL}/profile/update/${userId}`, {
        method: 'POST',
        credentials: 'include',
        body: formDataObj
      });
      
      console.log('Profile update response status:', response.status);
      
      const data = await response.json();
      console.log('Profile update response data:', data);
      
      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }
      
      // Check if the response indicates success (either explicitly or by status code)
      if (data.success || response.status >= 200 && response.status < 300) {
        // Show success message and redirect after a short delay
        const successMsg = data.message || 'Profile updated successfully!';
        setSuccessMessage(successMsg);
        console.log(successMsg);
        
        // Force clear localStorage cache if any
        localStorage.removeItem('profileData');
        
        // Set a flag that the profile was updated (for cross-tab communication)
        localStorage.setItem('profileUpdated', Date.now().toString());
        
        // Redirect after a short delay
        setTimeout(() => {
          // Use replace instead of push to force a fresh load
          navigate('/profile/', { replace: true, state: { forceRefresh: true } });
        }, 1500);
      } else {
        throw new Error(data.message || 'Failed to update profile');
      }
    } catch (err) {
      console.error('Error updating profile:', err);
      
      // Don't treat success messages as errors
      if (err.message && err.message.toLowerCase().includes('success')) {
        setSuccessMessage(err.message);
        
        // Force clear localStorage cache
        localStorage.removeItem('profileData');
        
        // Set a flag that the profile was updated (for cross-tab communication)
        localStorage.setItem('profileUpdated', Date.now().toString());
        
        // Still redirect to profile page after a short delay
        setTimeout(() => {
          navigate('/profile/', { replace: true, state: { forceRefresh: true } });
        }, 1500);
      } else {
        setSaveError(err.message || 'Failed to update profile. Please try again later.');
      }
    } finally {
      setSaving(false);
    }
  };

  const goBack = () => {
    navigate(-1);
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}></div>
        <p>Loading profile data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorMessage}>{error}</p>
        <button onClick={goBack} className={styles.backButton}>
          <FontAwesomeIcon icon={faArrowLeft} /> Go Back
        </button>
      </div>
    );
  }

  return (
    <div className={styles.editProfileContainer}>
      <div className={styles.header}>
        <button onClick={goBack} className={styles.backButton}>
          <FontAwesomeIcon icon={faArrowLeft} />
        </button>
        <h1 className={styles.title}>Edit Your Profile</h1>
      </div>

      <form onSubmit={handleSubmit} className={styles.profileForm}>
        {/* Cover Photo Section */}
        <div className={styles.coverPhotoSection}>
          {coverPhotoPreview ? (
            <img 
              src={coverPhotoPreview} 
              alt="Cover" 
              className={styles.coverPhoto} 
            />
          ) : (
            <div className={styles.coverPhotoPlaceholder}>
              <label htmlFor="cover-photo" className={styles.coverPhotoUploadButton}>
                <FontAwesomeIcon icon={faPlus} />
                <span>Add Cover Photo</span>
              </label>
            </div>
          )}
          <input
            type="file"
            id="cover-photo"
            accept="image/*"
            onChange={handleCoverPhotoChange}
            className={styles.fileInput}
          />
        </div>
        
        {/* Profile Image Section */}
        <div className={styles.imageSection}>
          <div className={styles.profileImageContainer}>
            {profileImagePreview && (
              <img 
                src={profileImagePreview} 
                alt="Profile" 
                className={styles.profileImage} 
              />
            )}
            <label htmlFor="profile-image" className={styles.imageUploadButton}>
              <FontAwesomeIcon icon={faPlus} />
            </label>
            <input
              type="file"
              id="profile-image"
              accept="image/*"
              onChange={handleProfileImageChange}
              className={styles.fileInput}
            />
          </div>
        </div>

        <div className={styles.formFields}>
          <div className={styles.formGroup}>
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter Your Username"
              className={styles.formInput}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="hometown">Hometown</label>
            <input
              type="text"
              id="hometown"
              name="hometown"
              value={formData.hometown}
              onChange={handleInputChange}
              placeholder="Enter Your Hometown"
              className={styles.formInput}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="current_location_city">Current City</label>
            <input
              type="text"
              id="current_location_city"
              name="current_location_city"
              value={formData.current_location_city}
              onChange={handleInputChange}
              placeholder="Enter Your Current City"
              className={styles.formInput}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              name="bio"
              value={formData.bio}
              onChange={handleInputChange}
              placeholder="Enter Your Bio"
              className={styles.formTextarea}
              rows="4"
            ></textarea>
          </div>
        </div>

        {saveError && (
          <div className={styles.errorMessage}>{saveError}</div>
        )}

        {successMessage && (
          <div className={styles.successMessage}>{successMessage}</div>
        )}

        <button 
          type="submit" 
          className={styles.saveButton}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
    </div>
  );
};

export default EditProfilePage;
