import React, { useMemo, useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom';
import '../Styles/custom/navBar.css'
import sproutlyLogo from '../Images/sproutly-logo.svg';
import sproutlyText from '../Images/sproutly-text.svg';

function NavBar() {
	const [showDropdown, setShowDropdown] = useState(false);
	const [isLoggedIn, setIsLoggedIn] = useState(true);
	const [userName] = useState("Vy");
	const dropdownRef = useRef<HTMLDivElement>(null);
	
	const location = useLocation();
	const navigate = useNavigate();

	useEffect(() => {
		// Close dropdown when clicking outside
		const handleClickOutside = (event: MouseEvent) => {
			if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
				setShowDropdown(false);
			}
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => {
			document.removeEventListener('mousedown', handleClickOutside);
		};
	}, []);

	const pageArray = useMemo(() => {
		return [
			{
				name: 'Home',
				path: '/',
			},
			{
				name: 'About',
				path: '/about',
			},
			{
				name: 'FAQ',
				path: '/faq',
			}
		]
	}, []);

	const handleLogout = () => {
		localStorage.removeItem('token');
		localStorage.removeItem('userDetails');
		setIsLoggedIn(false);
		navigate('/login');
		setShowDropdown(false);
	};

	const toggleDropdown = () => {
		setShowDropdown(!showDropdown);
	};

	const handleSettingsClick = () => {
		navigate('/settings');
		setShowDropdown(false);
	};

	return (
		<div className='navbar font-poppins'>
			<div onClick={()=>navigate('/')} className='sproutly-logo-decoration'>
				<img className='sproutly-logo' src={sproutlyLogo} alt='error img'/>
				<img className='sproutly-text' src={sproutlyText} alt='error img'/>
			</div>
			<div className='navbar-link-container'>
				{pageArray.map((page, index)=>{
					return <Link key={index} className={`navbar-link${location.pathname===page.path? ' text-white': ''}`} to={page.path}>{page.name}</Link>
				})}
			</div>
			
			{isLoggedIn ? (
				<div className="profile-dropdown" ref={dropdownRef}>
					<button onClick={toggleDropdown} className='profile-button'>
						Hi, {userName}
					</button>
					{showDropdown && (
						<div className="dropdown-menu">
							<button onClick={handleSettingsClick} className="dropdown-item">Settings</button>
							<button onClick={handleLogout} className="dropdown-item logout">Log Out</button>
						</div>
					)}
				</div>
			) : (
				<button onClick={()=>navigate('/login')} className='navbar-login-logout-button'>Log In</button>
			)}
		</div>
	)
}

export default NavBar;