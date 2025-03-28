import React, { useState } from 'react';
import '../Styles/custom/loginPage.css'; 
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';
import googleLogo from '../Images/google-logo.svg'
import { LoginObject } from '../Interfaces/AuthInterfaces';
import authController from '../Controller/AuthController';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import handleApiError from '../Utils/apiService';

function LoginPage() {

  const [loginObject, setLoginObject] = useState<LoginObject>({
    username: '',
    userpassword: '',
  });

  const navigate = useNavigate();

  const onLoginObjectChange =(key: string, value: string)=>{
    const newObject: LoginObject = {
      ...loginObject,
      [key]: value
    };

    setLoginObject(newObject);
  }

  const onSubmit = async (body: LoginObject) => {
    try {
      const response = await authController.login(body);
      toast.success("Login Successful", {
        position: 'top-right',
      });
      localStorage.setItem('access_token', response.data.access_token);
      const userDetailsResp = await authController.getUserDetails(body.username);
      localStorage.setItem('userDetails', JSON.stringify(userDetailsResp.data));
      navigate('/');

    } catch (error:unknown) {
      handleApiError(error);
    }
    
  }

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
          <label htmlFor="username">Username *</label>
          <input type="text" id="username" name="username" placeholder="Enter your username" value={loginObject.username} onChange={(e)=>onLoginObjectChange('username', e.target.value)} required />

          <label htmlFor="password">Password *</label>
          <input type="password" id="password" name="password" placeholder="Enter your password" value={loginObject.userpassword} onChange={(e)=>onLoginObjectChange('userpassword', e.target.value)} required />

          <button type='submit' className="login-btn" onClick={(e)=>{
              e.preventDefault();
              onSubmit(loginObject)
            }}>Log In</button>
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