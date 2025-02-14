import React from 'react'
<<<<<<< HEAD

function NavBar() {
  return (
    <div>NavBar</div>
=======
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
>>>>>>> fe68087a11103b291e8a14f454bdff774de1db60
  )
};

export default NavBar;