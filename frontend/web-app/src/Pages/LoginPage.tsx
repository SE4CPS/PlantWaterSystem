import React, { useState } from 'react';
import '../Styles/custom/loginPage.css'; 
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';
import googleLogo from '../Images/google-logo.svg'
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import apiService from '../Services/apiService';

function LoginPage() {
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });

  const navigate = useNavigate();

  const handleInputChange = (key: string, value: string) => {
    setCredentials({
      ...credentials,
      [key]: value
    });
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const { username, password } = credentials;
      const tokenResponse = await apiService.getToken(username, password);
      
      // Store token
      localStorage.setItem('token', tokenResponse.access_token);
      
      // Get user details
      const userData = await apiService.getUser(username);
      localStorage.setItem('userDetails', JSON.stringify(userData));
      
      toast.success("Login Successful");
      navigate('/');
    } catch {
      // Login error, toast notification handled in API service
    }
  }

  return (
    <div className="login-wrapper">
      <div className="logo-container">
        <img src={sproutlyLogo} alt="Sproutly Logo" className="logo" />
        <img src={sproutlyText} alt="Sproutly Text" className="sproutly-text" />
      </div>

      <div className="login-container">
        <h2 className="title">Log In</h2>

        <button className="google-login">
          <img 
            src={googleLogo} 
            alt="Google Logo" 
          />
          Sign in with Google
        </button>

        <div className="divider">
          <hr /> <span>or</span> <hr />
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username *</label>
          <input 
            type="text" 
            id="username" 
            name="username" 
            placeholder="Enter your username" 
            value={credentials.username} 
            onChange={(e) => handleInputChange('username', e.target.value)} 
            required 
          />

          <label htmlFor="password">Password *</label>
          <input 
            type="password" 
            id="password" 
            name="password" 
            placeholder="Enter your password" 
            value={credentials.password} 
            onChange={(e) => handleInputChange('password', e.target.value)} 
            required 
          />

          <button type='submit' className="login-btn">Log In</button>
        </form>

        <div className="footer-links">
          <a href="/signup">Don&rsquo;t have an account?</a>
          <a href="/forgot-password">Forgot your password?</a>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;