import React, { useMemo } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom';
import '../Styles/custom/navBar.css'

function NavBar() {

	const location = useLocation();

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
	}, [])

	return (
		<>
			<div className='navbar'>
				<div>Sproutly</div>
				<div className='navbar-link-container'>
					{pageArray.map((page, index)=>{
						return <Link key={index} className={`navbar-link${location.pathname===page.path? ' text-white': ''}`} to={page.path}>{page.name}</Link>
					})}
				</div>
				<button className='navbar-login-logout-button'>Log In</button>
			</div>
			<Outlet />
		</>
	)
};

export default NavBar;