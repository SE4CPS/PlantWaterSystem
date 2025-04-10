import React, { useState } from 'react';
import '../Styles/custom/settingsPage.css';
import { useNavigate } from 'react-router-dom';
// Removed apiService import as it's no longer needed for auth check
// import apiService, { User } from '../Services/apiService'; 
// Removed toast import if not used elsewhere
// import { toast } from 'react-toastify';

// Simplified User interface if only using dummy data
interface User {
  name: string;
  phoneNumber: string;
  email: string;
  password: string;
}

function SettingsPage() {
  const [notifications, setNotifications] = useState({
    sms: true,
    email: false
  });
  // Using static dummy data since auth is removed
  const [userData] = useState<User>({
    name: "Vy N.",
    phoneNumber: "+1 (234) 567-891",
    email: "vn1234567@gmail.com",
    password: "************"
  });
  // Removed loading state as data is static now
  // const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Removed useEffect for fetching user data
  // useEffect(() => { ... fetch logic removed ... }, [navigate]);

  const handleCheckboxChange = (type: 'sms' | 'email') => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleLogout = () => {
    // Simulate logout by clearing potentially stored items (optional)
    localStorage.removeItem('token');
    localStorage.removeItem('userDetails');
    // Navigate to login or home page as appropriate
    navigate('/login'); 
  };

  // Removed loading check
  // if (loading) { ... }

  return (
    <div className="page-container">
      {/* Settings Content */}
      <div className="settings-container">
        <h1>Settings</h1>
        
        {/* Personal Information Section */}
        <div className="settings-section">
          <div className="section-header">
            <h2>Personal Information</h2>
          </div>
          <div className="personal-info">
            <div className="info-row">
              <label>Name:</label>
              <span>{userData.name}</span>
            </div>
            <div className="info-row">
              <label>Phone number:</label>
              <span>{userData.phoneNumber}</span>
            </div>
            <div className="info-row">
              <label>Email:</label>
              <span>{userData.email}</span>
            </div>
            <div className="info-row">
              <label>Password:</label>
              <span>{userData.password}</span>
            </div>
          </div>
        </div>
        
        {/* Communication Preferences Section */}
        <div className="settings-section">
          <div className="section-header">
            <h2>Communication Preferences</h2>
          </div>
          <p>Sproutly will send you notifications when your plants need attention.</p>
          <div className="preferences">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={notifications.sms} 
                onChange={() => handleCheckboxChange('sms')} 
              />
              SMS
            </label>
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={notifications.email} 
                onChange={() => handleCheckboxChange('email')} 
              />
              Email
            </label>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="action-buttons">
          <button className="logout-button" onClick={handleLogout}>Log Out</button>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;