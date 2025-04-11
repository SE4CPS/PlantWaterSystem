import React, { useEffect, useState } from 'react'
import { UserDetails, UserSettings } from '../Interfaces/AuthInterfaces';
import { useNavigate } from 'react-router-dom';
import '../Styles/custom/settingsPage.css'

function SettingsPage() {

  const [userDetails, setUserDetails] = useState<UserSettings>({
    email: '',
    firstname: '',
    lastname: '',
    phonenumber: '',
    username: '',
  });

  const navigate = useNavigate();

  useEffect(() => {
    const userstring = localStorage.getItem('userDetails');
    if(userstring){
      const userData: UserDetails = userstring? JSON.parse(userstring) : userDetails;
      setUserDetails({
        email: userData.email,
        firstname: userData.firstname,
        lastname: userData.lastname,
        phonenumber: userData.phonenumber,
        username: userData.username,
      });
    }
    else navigate('/')
  }, [userDetails, navigate]);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <div className="settings-page-container">
      <div className="settings-container">
        <h1>Settings</h1>
        
        <div className="settings-section">
          <h2>Personal Information</h2>
          <div className="settings-info-group">
            <label>Name</label>
            <div className="settings-info-value">{userDetails.firstname} {userDetails.lastname}</div>
          </div>
          <div className="settings-info-group">
            <label>Phone Number</label>
            <div className="settings-info-value">{userDetails.phonenumber}</div>
          </div>
          <div className="settings-info-group">
            <label>Email</label>
            <div className="settings-info-value">{userDetails.email}</div>
          </div>
          <div className="settings-info-group">
            <label>Username</label>
            <div className="settings-info-value">{userDetails.username}</div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Communication Preferences</h2>
          <div className="settings-preference-group">
            <label className="settings-checkbox-label">
              <input type="checkbox" defaultChecked />
              <span>SMS Notifications</span>
            </label>
            <label className="settings-checkbox-label">
              <input type="checkbox" defaultChecked />
              <span>Email Notifications</span>
            </label>
          </div>
        </div>

        <div className="settings-button-group">
          <button className="settings-logout-button" onClick={()=>handleLogout()}>
            Log Out
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage