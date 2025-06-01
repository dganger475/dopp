import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaCamera, FaTimes, FaCheck, FaSpinner, FaUser, FaPen, FaSave } from 'react-icons/fa';
import styles from './EditProfilePage.module.css';
import API_BASE_URL, { getApiUrl } from '../config/api';
import ProfileImageBorder from './profileimageborder';
import UsernamePill from './usernamepill';
import UsernamePillText from './usernamepilltext';
import UniversalCard from '../components/UniversalCard';

const EditProfilePage = () => {
  const navigate = useNavigate();
  
  // Main state
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Editable fields
  const [editMode, setEditMode] = useState({
    username: false,
    fullName: false,
    bio: false,
    currentCity: false,
    hometown: false
  });
  
  // Form data
  const [formData, setFormData] = useState({
    fullName: '',
    username: '',
    bio: '',
    currentCity: '',
    hometown: '',
    email: '',
    phone: '',
    memberSince: new Date().toISOString()
  });
  
  // Images
  const [profileImage, setProfileImage] = useState(null);
  const [coverImage, setCoverImage] = useState(null);
  
  // Matches
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [matchesError, setMatchesError] = useState(null);
  
  // Refs for file inputs
  const profileImageInputRef = useRef(null);
  const coverImageInputRef = useRef(null);

  // Fetch user data on component mount
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        console.log('Fetching user profile data...');
        
        const response = await fetch(`${API_BASE_URL}/api/profile/data`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Server error response:', errorText);
          throw new Error(`Failed to fetch user data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Profile data received:', data);
        
        if (!data.success) {
          throw new Error(data.message || 'Failed to fetch user data');
        }
        
        if (!data.user) {
          throw new Error('No user data received');
        }
        
        // Store the full response
        setUserProfile(data);
        
        // Extract user data
        const user = data.user;
        
        // Set form data for editing
        setFormData({
          fullName: user.full_name || '',
          username: user.username || '',
          bio: user.bio || '',
          currentCity: user.current_city || '',
          hometown: user.hometown || '',
          email: user.email || '',
          phone: user.phone || '',
          memberSince: user.memberSince || new Date().toISOString()
        });
        
        // Set profile image if available
        if (user.profile_image_url) {
          setProfileImage(user.profile_image_url);
        }
        
        // Set cover image if available
        if (user.cover_photo_url || user.cover_photo) {
          setCoverImage(user.cover_photo_url || user.cover_photo);
        }
        
      } catch (error) {
        console.error('Error fetching user data:', error);
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    const fetchMatches = async () => {
      try {
        const matchesResponse = await fetch(`${API_BASE_URL}/social/matches/api/matches/sync`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        if (!matchesResponse.ok) {
          throw new Error('Failed to fetch matches');
        }
        
        const data = await matchesResponse.json();
        console.log('Matches data received:', data);
        
        if (data.success && data.matches) {
          setMatches(data.matches);
        } else {
          setMatches([]);
        }
      } catch (err) {
        console.error('Error fetching matches:', err);
        setMatchesError(err.message);
      } finally {
        setLoadingMatches(false);
      }
    };
    
    fetchUserData();
    fetchMatches();
  }, []);

  // Initialize form data from user profile
  useEffect(() => {
    if (userProfile && userProfile.user) {
      const user = userProfile.user;
      
      // Set form data for editing with safe fallbacks
      setFormData({
        fullName: user.full_name || user.fullName || '',
        username: user.username || '',
        bio: user.bio || '',
        currentCity: user.current_city || user.currentCity || '',
        hometown: user.hometown || '',
        email: user.email || '',
        phone: user.phone || '',
        memberSince: user.memberSince || user.member_since || new Date().toISOString()
      });
      
      // Set profile image with proper fallback - never use default images for face matching
      if (user.profile_image_url) {
        setProfileImage(user.profile_image_url);
      }
      
      if (user.cover_photo_url || user.cover_photo) {
        setCoverImage(user.cover_photo_url || user.cover_photo);
      }
    }
  }, [userProfile]);

  // Toggle edit mode for a field
  const toggleEditMode = (field) => {
    setEditMode(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle profile image change
  const handleProfileImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, or GIF)');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image size should be less than 5MB');
      return;
    }
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setProfileImage(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Handle cover image change
  const handleCoverImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, or GIF)');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image size should be less than 5MB');
      return;
    }
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setCoverImage(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Save a specific field
  const saveField = (field) => {
    // Validate field if needed
    if (field === 'username' && !/^[a-zA-Z0-9_.-]+$/.test(formData.username)) {
      setError('Username can only contain letters, numbers, ., -, and _');
      return;
    }
    
    // Close edit mode for this field
    toggleEditMode(field);
  };

  // Handle form submission
  const handleSubmit = async () => {
    setIsSaving(true);
    setError(null);
    
    try {
      // Create FormData object for file uploads
      const formDataObj = new FormData();
      
      // Append all form fields
      formDataObj.append('full_name', formData.fullName);
      formDataObj.append('username', formData.username);
      formDataObj.append('bio', formData.bio);
      formDataObj.append('current_city', formData.currentCity);
      formDataObj.append('hometown', formData.hometown);
      formDataObj.append('email', formData.email);
      formDataObj.append('phone', formData.phone);
      
      // Handle profile image - NEVER use default profile images for face matching
      if (profileImage) {
        if (typeof profileImage === 'string' && profileImage.startsWith('data:')) {
          // Convert base64 to blob
          const blob = await fetch(profileImage).then(r => r.blob());
          formDataObj.append('profile_image', blob, 'profile_image.jpg');
        } else if (profileImage instanceof File) {
          formDataObj.append('profile_image', profileImage);
        } else if (typeof profileImage === 'string') {
          // It's a URL, we'll just send the URL and let the server handle it
          formDataObj.append('profile_image_url', profileImage);
        }
      }
      
      // Handle cover image
      if (coverImage) {
        if (typeof coverImage === 'string' && coverImage.startsWith('data:')) {
          const blob = await fetch(coverImage).then(r => r.blob());
          formDataObj.append('cover_photo', blob, 'cover_photo.jpg');
        } else if (coverImage instanceof File) {
          formDataObj.append('cover_photo', coverImage);
        } else if (typeof coverImage === 'string') {
          formDataObj.append('cover_photo_url', coverImage);
        }
      }
      
      console.log('Submitting profile data...');
      
      // Send to server using the profile update endpoint
      const userId = userProfile?.user?.id;
      if (!userId) {
        throw new Error('User ID not found');
      }
      
      const response = await fetch(getApiUrl(`/profile/update/${userId}`), {
        method: 'POST',
        credentials: 'include',
        body: formDataObj
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error response:', errorText);
        throw new Error(`Failed to update profile: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Profile update result:', result);
      
      // Show success message
      setSaveSuccess(true);
      
      // Redirect after a delay
      setTimeout(() => {
        navigate('/profile');
      }, 2000);
      
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.message || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/profile');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <FaSpinner className="fa-spin" size={40} color="var(--dopple-blue)" />
        <div>Loading profile data...</div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className={styles.errorContainer}>
        <div>Error: {error}</div>
        <div className={styles.errorActions}>
          <button onClick={() => window.location.href = '/login'} className={styles.loginButton}>
            Log In
          </button>
          <button onClick={() => navigate('/profile')} className={styles.returnButton}>
            Return to Profile
          </button>
          <button 
            onClick={() => {
              // Create a dummy profile for testing
              setUserProfile({
                user: {
                  username: 'testuser',
                  full_name: 'Test User',
                  bio: 'This is a test bio',
                  current_city: 'Test City',
                  hometown: 'Test Hometown',
                  memberSince: new Date().toISOString()
                }
              });
              setError(null);
            }} 
            className={styles.demoButton}
          >
            Use Demo Data
          </button>
        </div>
      </div>
    );
  }
  
  // If no user profile data
  if (!userProfile || !userProfile.user) {
    return (
      <div className={styles.errorContainer}>
        <div>No profile data available.</div>
        <button onClick={() => navigate('/profile')} className={styles.returnButton}>
          Return to Profile
        </button>
      </div>
    );
  }
  
  // Get user data
  const userData = userProfile.user;
  
  // Prepare image URLs
  const profileImageUrl = profileImage || 
    (userData && userData.profile_image_url ? 
      (userData.profile_image_url.startsWith('http') ? userData.profile_image_url : getApiUrl(userData.profile_image_url)) : 
      null);
      
  const coverPhotoUrl = coverImage || 
    (userData && userData.cover_photo_url ? 
      (userData.cover_photo_url.startsWith('http') ? 
        userData.cover_photo_url : 
        getApiUrl(userData.cover_photo_url)) : 
      getApiUrl('/static/images/default_cover_photo.png'));

  // Add cache-busting to the cover photo URL
  const coverPhotoUrlWithCacheBust = `${coverPhotoUrl}${coverPhotoUrl.includes('?') ? '&' : '?'}t=${Date.now()}`;

  // Log the cover photo URL for debugging
  console.log('Cover photo URL:', coverPhotoUrl);
  console.log('Cover photo URL with cache bust:', coverPhotoUrlWithCacheBust);

  return (
    <div className={styles.editProfilePage}>
      {/* Hidden file inputs */}
      <input
        type="file"
        ref={profileImageInputRef}
        style={{ display: 'none' }}
        accept="image/*"
        onChange={handleProfileImageChange}
      />
      <input
        type="file"
        ref={coverImageInputRef}
        onChange={handleCoverImageChange}
        style={{ display: 'none' }}
        accept="image/*"
      />
      
      {/* Cover photo section */}
      <div className={styles.coverPhotoContainer}>
        <div 
          className={styles.coverPhoto}
          style={{ 
            backgroundImage: `url(${coverPhotoUrlWithCacheBust})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat'
          }}
        ></div>
        <button 
          className={styles.editCoverButton}
          onClick={() => coverImageInputRef.current.click()}
        >
          <FaCamera /> Change Cover
        </button>
      </div>
      
      {/* Profile image positioned over cover photo - no longer in a circle container */}
      <div className={styles.profileSection}>
        {profileImageUrl ? (
          <div className={styles.profileImageWrapper}>
            <ProfileImageBorder image={profileImageUrl} />
            <button 
              className={styles.editProfileImageButton}
              onClick={() => profileImageInputRef.current.click()}
            >
              <FaCamera />
            </button>
          </div>
        ) : (
          <div className={styles.defaultProfileImage}>
            <div style={{width: 180, height: 180, background: '#eee', color: '#888', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 10, fontWeight: 'bold', fontSize: 14, border: '6px solid #000000', boxShadow: '0 3px 6px rgba(0, 0, 0, 0.2)', marginTop: '-40px', position: 'relative', zIndex: 10}}>
              No profile image
              <button 
                className={styles.editProfileImageButton}
                onClick={() => profileImageInputRef.current.click()}
              >
                <FaCamera />
              </button>
            </div>
          </div>
        )}
        
        {/* Username pill with edit mode */}
        <div className={styles.usernamePillRow}>
          {editMode.username ? (
            <div className={styles.editableField}>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className={styles.editableInput}
                placeholder="Enter username"
              />
              <div className={styles.editButtons}>
                <button onClick={() => saveField('username')} className={styles.saveButton}>
                  <FaCheck />
                </button>
                <button onClick={() => toggleEditMode('username')} className={styles.cancelButton}>
                  <FaTimes />
                </button>
              </div>
            </div>
          ) : (
            <UsernamePill onClick={() => toggleEditMode('username')}>
              <UsernamePillText text={formData.username} />
              <span className={styles.editIcon}><FaPen size={12} /></span>
            </UsernamePill>
          )}
        </div>
      </div>
      
      {/* Info row with Member Since on left, location info on right */}
      <div className={styles.infoRow}>
        <div className={styles.memberSinceContainer}>
          <span className={styles.memberSinceLabel}>Member Since: </span>
          <span>
            {formData.memberSince 
              ? new Date(formData.memberSince).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
              : new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </span>
        </div>
        
        <div className={styles.locationContainer}>
          {/* Current City (Editable) */}
          {editMode.currentCity ? (
            <div className={styles.editableField}>
              <span className={styles.locationLabel}>Current City: </span>
              <input
                type="text"
                name="currentCity"
                value={formData.currentCity}
                onChange={handleChange}
                className={styles.editableInput}
                placeholder="Enter your current city"
              />
              <div className={styles.editButtons}>
                <button onClick={() => saveField('currentCity')} className={styles.saveButton}>
                  <FaCheck />
                </button>
                <button onClick={() => toggleEditMode('currentCity')} className={styles.cancelButton}>
                  <FaTimes />
                </button>
              </div>
            </div>
          ) : (
            <div onClick={() => toggleEditMode('currentCity')} className={styles.editableDisplay}>
              <span className={styles.locationLabel}>Current City: </span>
              <span>{formData.currentCity || 'Not specified'}</span>
              <FaPen className={styles.editIcon} size={12} />
            </div>
          )}
          
          <br />
          
          {/* Hometown (Editable) */}
          {editMode.hometown ? (
            <div className={styles.editableField}>
              <span className={styles.locationLabel}>Hometown: </span>
              <input
                type="text"
                name="hometown"
                value={formData.hometown}
                onChange={handleChange}
                className={styles.editableInput}
                placeholder="Enter your hometown"
              />
              <div className={styles.editButtons}>
                <button onClick={() => saveField('hometown')} className={styles.saveButton}>
                  <FaCheck />
                </button>
                <button onClick={() => toggleEditMode('hometown')} className={styles.cancelButton}>
                  <FaTimes />
                </button>
              </div>
            </div>
          ) : (
            <div onClick={() => toggleEditMode('hometown')} className={styles.editableDisplay}>
              <span className={styles.locationLabel}>Hometown: </span>
              <span>{formData.hometown || 'Not specified'}</span>
              <FaPen className={styles.editIcon} size={12} />
            </div>
          )}
        </div>
      </div>
      
      {/* Bio section (Editable) */}
      <div className={styles.bioSection}>
        <div className={styles.bioLabel}>Bio:</div>
        {editMode.bio ? (
          <div className={styles.editableBioField}>
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              className={styles.editableBioInput}
              placeholder="Tell us about yourself"
              rows={4}
            />
            <div className={styles.editButtons}>
              <button onClick={() => saveField('bio')} className={styles.saveButton}>
                <FaCheck />
              </button>
              <button onClick={() => toggleEditMode('bio')} className={styles.cancelButton}>
                <FaTimes />
              </button>
            </div>
          </div>
        ) : (
          <div onClick={() => toggleEditMode('bio')} className={styles.bioContainer}>
            {formData.bio || 'No bio provided. Click to add one.'}
            <FaPen className={styles.editIcon} size={12} />
          </div>
        )}
      </div>
      
      {/* Save Changes Button */}
      <div className={styles.saveChangesContainer}>
        {error && <div className={styles.errorMessage}>{error}</div>}
        {saveSuccess && <div className={styles.successMessage}>Profile updated successfully!</div>}
        
        <div className={styles.buttonRow}>
          <button 
            className={styles.cancelButton}
            onClick={handleCancel}
          >
            Cancel
          </button>
          <button 
            className={styles.saveButton}
            onClick={handleSubmit}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <FaSpinner className="fa-spin" style={{ marginRight: '8px' }} />
                Saving...
              </>
            ) : (
              <>
                <FaSave style={{ marginRight: '8px' }} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Matches Section Removed */}
      <div className={styles.matchesSection}>
        <h2>Your Matches</h2>
        <div className={styles.noMatches}>Matches display temporarily disabled</div>
      </div>
    </div>
  );
};

export default EditProfilePage;
