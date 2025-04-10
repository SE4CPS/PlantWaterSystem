import React, { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import NavBar from './NavBar'; // Assuming NavBar is in the same directory

// Define the MainLayout component directly within ProtectedRoute or import it
const MainLayout = () => (
  <>
    <NavBar />
    <Outlet /> {/* This renders the matched child route element */}
  </>
);

function ProtectedRoute() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null); // Use null to indicate loading state

  useEffect(() => {
    // Check for token in localStorage
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token); // Set to true if token exists, false otherwise
  }, []);

  if (isAuthenticated === null) {
    // Still checking authentication, show loading indicator or nothing
    return <div className="loading">Loading...</div>; // Or return null;
  }

  if (!isAuthenticated) {
    // Not authenticated, redirect to login page
    return <Navigate to="/login" replace />;
  }

  // Authenticated, render the main layout which includes NavBar and the child route
  return <MainLayout />;
}

export default ProtectedRoute; 