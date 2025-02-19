import React from 'react'
import { Link, Outlet } from 'react-router-dom';

function NavBar() {
  return (
    <div>
      <div>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
        <Link to="/faq">FAQ</Link>
      </div>
      <Outlet />
    </div>
  )
};

export default NavBar;