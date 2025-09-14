import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { useNavigate } from 'react-router-dom';

function Profile() {
  const { user, logout } = useAuth();
  const [userDetails, setUserDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/profile', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUserDetails(data.user);
      } else {
        setError('Failed to load profile information');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Profile fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="loading-message">Loading profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-container">
        <div className="error-message">{error}</div>
        <button onClick={handleBackToHome} className="btn-secondary">
          Back to Home
        </button>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <h2>My Profile</h2>
      
      <div className="welcome-section">
        <h3>Welcome back, {userDetails?.first_name || user?.firstName}!</h3>
        <p>Here's your account information:</p>
      </div>

      <div className="profile-info">
        <div className="info-section">
          <h4>Personal Information</h4>
          <div className="info-row">
            <label>Name:</label>
            <span>{userDetails?.first_name || user?.firstName} {userDetails?.last_name || user?.lastName}</span>
          </div>
          <div className="info-row">
            <label>Email:</label>
            <span>{userDetails?.email || user?.email}</span>
          </div>
          {userDetails?.gender && (
            <div className="info-row">
              <label>Gender:</label>
              <span>{userDetails.gender}</span>
            </div>
          )}
          {userDetails?.age && (
            <div className="info-row">
              <label>Age:</label>
              <span>{userDetails.age}</span>
            </div>
          )}
          {userDetails?.phone && (
            <div className="info-row">
              <label>Phone:</label>
              <span>{userDetails.phone}</span>
            </div>
          )}
          {userDetails?.address && (
            <div className="info-row">
              <label>Address:</label>
              <span>{userDetails.address}</span>
            </div>
          )}
          {userDetails?.created_at && (
            <div className="info-row">
              <label>Member since:</label>
              <span>{new Date(userDetails.created_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>

      <div className="profile-actions">
        <button onClick={handleBackToHome} className="btn-secondary">
          Back to Home
        </button>
        <button onClick={handleLogout} className="btn-logout">
          Logout
        </button>
      </div>
    </div>
  );
}

export default Profile;