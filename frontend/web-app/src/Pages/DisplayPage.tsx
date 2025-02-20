import React from 'react'
import '../Styles/custom/displayPage.css'
import display_img_1 from '../Images/display-1.png'
import display_img_2 from '../Images/display-2.png'
import display_img_3 from '../Images/display-3.png'
import { useNavigate } from 'react-router-dom'

function DisplayPage() {
  const navigate = useNavigate();
  return (
    <div className='displayPage font-poppins'>
      <div className='displayPage-text-decoration'>
        <div className='displayPage-sales-text'>
          Tracking with Sproutly <b className='highlighted-text'>helps your plants thrive</b> by keeping them healthy, hydrated & happy.
        </div>
        <button onClick={()=>navigate('/login')} className='displayPage-login-button'>
          Log In
        </button>
        <div className='displayPage-signup-text'>
          Don&rsquo;t have an account? <div onClick={()=>navigate('/signup')} className='signup-text'>Sign Up here</div>
        </div>
      </div>
      <div className='displayPage-image-decoration'>
        <div className='displayPage-upper-image'>
          <img className='displayPage-image-3' src={display_img_3} alt='error img' />
          <img className='displayPage-image-2' src={display_img_2} alt='error img' />
        </div>
        <img className='displayPage-image-1' src={display_img_1} alt='error img' />
      </div>
    </div>
  )
}

export default DisplayPage