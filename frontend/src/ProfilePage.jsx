import React, { useState, useEffect } from 'react';
import API_BASE_URL from "./config/api";
import { useNavigate } from 'react-router-dom';
import styles from './ProfilePage.module.css';
import CoverPhoto from './profilepage/coverphoto';
import ProfileImageBorder from './profilepage/profileimageborder';
import UsernamePill from './profilepage/usernamepill';
import UsernamePillText from './profilepage/usernamepilltext';
import UsersFullName from './profilepage/usersfullname';
import BioContainer from './profilepage/biocontainer';
import BioText from './profilepage/biotext';
import CurrentCity from './profilepage/currentcity';
import Hometown from './profilepage/hometown';
import MemberSince from './profilepage/membersince';
import EditProfileButton from './profilepage/editprofilebutton';
import AddMatchButton from './profilepage/addmatchbutton';
import BioInput from './profilepage/bioinput';
import BioLable from './profilepage/biolable';
import MatchBadge1 from './profilepage/matchbadge/matchbadge1';
import MatchBadgeText from './profilepage/matchbadge/80percentmatchbadgetext';
import UniversalCard from './components/UniversalCard';

const MOBILE_BREAKPOINT = 768;

const ProfilePage = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [matchesError, setMatchesError] = useState(null);
  const navigate = useNavigate();

  // Remove existing styles from wrong server
  useEffect(() => {
    const removeWrongServerStyles = () => {
      const links = document.querySelectorAll('link[rel="stylesheet"][href]');
      links.forEach(link => {
        if (link.href.includes(':5173')) {
          link.remove();
        }
      });
    };
    removeWrongServerStyles();
  }, []);

  // Handle responsive layout
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch user data
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/profile/`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }
        const data = await response.json();
        if (data.success) {
          setUserProfile(data);
        } else {
          throw new Error(data.error || 'Failed to load user data');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };


    const fetchMatches = async () => {
      try {
        // Use API_BASE_URL for API requests only. Do not rewrite <img> src for CSS or fonts.

        const matchesResponse = await fetch(`${API_BASE_URL}/social/matches/api/matches/sync`, {
          credentials: 'include'
        });
        if (!matchesResponse.ok) {
          throw new Error('Failed to fetch matches');
        }
        const data = await matchesResponse.json();
        // Combine claimed and added matches
        const claimed = (data.claimed || []).map(m => ({ ...m, type: 'claimed' }));
        const added = (data.added || []).map(m => ({ ...m, type: 'added' }));
        setMatches([...claimed, ...added]);
      } catch (err) {
        setMatchesError(err.message);
      } finally {
        setLoadingMatches(false);
      }
    };

    fetchUserData();
    fetchMatches();
  }, []);

  if (loading) {
    return <div className="loading">Loading profile...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!userProfile) {
    return <div className="error">No profile data found.</div>;
  }

  // Use robust fallbacks for images
  const profileImageUrl = userProfile.image || '/static/images/default_profile.jpg';
  const coverPhotoUrl = userProfile.coverPhoto || '/static/images/default_cover_photo.png';
  // Ensure we're properly mounted at the expected route
  useEffect(() => {
    document.title = 'Profile | DoppleGanger';
  }, []);

  return (
    <div className={styles['profile-page']} style={{ fontFamily: 'Arial, Helvetica Neue, Helvetica, sans-serif' }}>
      {/* Cover photo at top, profile image overlaps */}
      <div
        className={styles.coverPhoto}
        style={{ backgroundImage: `url('${coverPhotoUrl}')` }}
      >
        <div className={styles.fixedProfileInfo}>
          <div className={styles.profileImageOuterWrap}>
            <div className={styles.profileImageContainer}>
              <ProfileImageBorder image={profileImageUrl} />
              <div className={styles.usernamePillRow}>
                <UsernamePill>
                  <UsernamePillText text={userProfile.username} />
                </UsernamePill>
              </div>
              <div className={styles.bioSection}>
                <BioContainer>
                  {userProfile.bio || 'No bio provided.'}
                </BioContainer>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Add Match button in top left */}
      <AddMatchButton profile={userProfile} className={`${styles.addMatchBtn} ${styles.fixedAddMatchBtn}`} />
      {/* Fixed Edit Profile button in top right */}
      <EditProfileButton onClick={() => navigate('/edit-profile')} className={`${styles.editProfileBtn} ${styles.fixedEditProfileBtn}`} />

      {/* Info row: member since left, city/hometown right */}
      <div className={styles.infoRow}>
        <div className={styles.cityHometown}>
          {userProfile.current_city && <span>{userProfile.current_city}</span>}
          {userProfile.hometown && (
            <span style={{ marginLeft: userProfile.current_city ? 8 : 0 }}>
              {userProfile.hometown}
            </span>
          )}
        </div>
      </div>

      {/* Matches grid at the bottom */}
      <div className={styles.matchesSection}>
        {loadingMatches ? (
          <div className="loading">Loading matches...</div>
        ) : matchesError ? (
          <div className="error">Error loading matches: {matchesError}</div>
        ) : matches.length > 0 ? (
          <div className={styles.matchesGrid}>
            {matches.map((match, index) => (
              <UniversalCard
                key={match.id || index}
                image={match.filename ? `${API_BASE_URL}/face/image/${match.id}` : '/default_profile.png'}
                username={match.username || (match.relationship === 'UNCLAIMED PROFILE' ? 'Unclaimed Profile' : 'Registered User')}
                label={match.relationship || 'REGISTERED USER'}
                labelColor={'#fff'}
                labelBg={match.relationship === 'UNCLAIMED PROFILE' ? 'var(--dopple-blue)' : 'var(--dopple-red)'}
                decade={match.decade || ''}
                state={match.state || ''}
                similarity={match.similarity !== undefined ? Math.round(match.similarity * 100) : undefined}
                isRegistered={match.relationship !== 'UNCLAIMED PROFILE'}
                className={match.relationship === 'UNCLAIMED PROFILE' ? styles.matchCardUnclaimed : styles.matchCardClaimed}
              />
            ))}
          </div>
        ) : null}
        <div className={styles.matchesFoundText} style={{ marginTop: 48, marginBottom: 0 }}>
          Matches Found: {matches.length}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
