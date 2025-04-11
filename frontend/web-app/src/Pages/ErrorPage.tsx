import React from 'react'
import '../Styles/custom/errorPage.css'
import errorImage from '../Images/error-1.png'
import sproutlyLogo from '../Images/sproutly-logo.svg'
import sproutlyText from '../Images/sproutly-text.svg'
import { useNavigate } from 'react-router-dom'

function ErrorPage() {

  const navigate = useNavigate();

  return (
    <div className="errorcontainer font-poppins">
        <div className='error-text-title'>404 Page Not Found</div>
        <p className='error-text-info'>Sorry, the page you are looking for does not exist.</p>
        <button onClick={()=>{
          if(localStorage.getItem('userDetails')) navigate('/app/dashboard')
          else navigate('/');
        }} className="error-return-home-btn">Return Home</button>
        <div className="errorplant-container">
            <img src={errorImage} alt="Sad Plant"/>
        </div>
        <div className="errorlogo">
            <img className='error-sproutly-logo' src={sproutlyLogo} alt="Sproutly logo"/>
            <img className='error-sproutly-text' src={sproutlyText} alt="Sproutly text"/>
        </div>
    </div>
  )
}

export default ErrorPage