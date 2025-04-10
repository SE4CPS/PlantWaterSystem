import React, { useEffect, useMemo, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import '../Styles/custom/navBar.css'
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';
import { UserDetails } from '../Interfaces/AuthInterfaces';

function NavBar() {

	const [userDetails, setUserDetails] = useState<null | UserDetails>(null);
	const [settingsToggle, setSettingsToggle] = useState(false);

	const location = useLocation();
	const navigate = useNavigate();

	useEffect(() => {
	  const userstring = localStorage.getItem('userDetails');
	  if(userstring){
		const user = JSON.parse(userstring);
		setUserDetails(user);
	  }
	}, []);

	const userLogOut = () => {
		setSettingsToggle(val => !val);
		localStorage.clear();
		navigate('/');
	}

	const pageArray = useMemo(() => {
		let navArray = [
			{
				name: 'About',
				path: '/app/about',
			},
			{
				name: 'FAQ',
				path: '/app/faq',
			}
		]

		if(userDetails){
			navArray = [
				{
					name: 'Home',
					path: '/app/dashboard',
				},
				...navArray,
			];
		}
		else{
			navArray = [
				{
					name: 'Login',
					path: '/',
				},
				...navArray,
			];
		}

		return navArray;
	}, [userDetails])

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
				<div className={settingsToggle ? 'navbar-settings-dropdown-container':''}>
					{
						!userDetails && <button onClick={()=>navigate('/')} className='navbar-login-logout-button'>Log In</button>
					}
					{
						userDetails && (
								<button onClick={()=>setSettingsToggle(settingsToggle => !settingsToggle)} className='navbar-login-logout-button'>Hi, {userDetails.firstname}</button>
						)
					}
					{
						settingsToggle && (
							<div className='navbar-settings-dropdown'>
								<button className='navbar-dropdown-settings-btn' onClick={()=>{
										setSettingsToggle(val => !val);
										navigate('/app/settings')
									}}>Settings</button>
								<button className='navbar-dropdown-logout-btn' onClick={()=>userLogOut()}>Log Out</button>
							</div>
						)
					}
				</div>
			</div>
			<Outlet />
		</>
	)
}

export default NavBar;