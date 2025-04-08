import React, { useMemo } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import '../Styles/custom/navBar.css'
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';

function NavBar() {

	const location = useLocation();

	const navigate = useNavigate();

	const pageArray = useMemo(() => {
		return [
			{
				name: 'Home',
				path: '/app/dashboard',
			},
			{
				name: 'About',
				path: '/app/about',
			},
			{
				name: 'FAQ',
				path: '/app/faq',
			}
		]
	}, [])

	return (
		<>
			<div className='navbar font-poppins'>
				<div onClick={()=>navigate('/display')} className='sproutly-logo-decoration'>
					<img className='sproutly-logo' src={sproutlyLogo} alt='error img'/>
					<img className='sproutly-text' src={sproutlyText} alt='error img'/>
				</div>
				<div className='navbar-link-container'>
					{pageArray.map((page, index)=>{
						return <Link key={index} className={`navbar-link${location.pathname===page.path? ' text-white': ''}`} to={page.path}>{page.name}</Link>
					})}
				</div>
				<button onClick={()=>navigate('/')} className='navbar-login-logout-button'>Log In</button>
			</div>
			<Outlet />
		</>
	)
}

export default NavBar;