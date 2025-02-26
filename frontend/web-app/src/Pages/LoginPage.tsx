import React from 'react';
import '../Styles/custom/loginPage.css'; 
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';
import googleLogo from '../Images/google-logo.svg'

function LoginPage() {
  return (
    <div className="login-wrapper">
      {}
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

        <form>
          <label htmlFor="email">Email *</label>
          <input type="email" id="email" name="email" placeholder="Enter your email" required />

          <label htmlFor="password">Password *</label>
          <input type="password" id="password" name="password" placeholder="Enter your password" required />

          <button type="submit" className="login-btn">Log In</button>
        </form>

        <div className="footer-links">
          <a href="/signup">Don’t have an account?</a>
          <a href="/forgot-password">Forgot your password?</a>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;