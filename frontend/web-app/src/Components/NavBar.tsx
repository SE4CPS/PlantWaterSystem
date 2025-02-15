import React from 'react'
import { Link, Outlet } from 'react-router-dom';
import '../Styles/custom/navBar.css'

function NavBar() {
	return (
		<>
			<div className='navbar'>
				<div>Sproutly</div>
				<div className='navbar-link-container'>
					<Link className='navbar-link text-white' to="/">Home</Link>
					<Link className='navbar-link' to="/about">About</Link>
					<Link className='navbar-link' to="/faq">FAQ</Link>
				</div>
				<div className='navbar-login-logout-button'>Log In</div>
			</div>
			<Outlet />
		</>
	)
};

export default NavBar;