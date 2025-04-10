import React from "react";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import LoginPage from "../Pages/LoginPage";
import HomePage from "../Pages/HomePage";
import PlantDetailPage from "../Pages/PlantDetailPage";
import AboutPage from "../Pages/AboutPage";
import FaqPage from "../Pages/FaqPage";
import ErrorPage from "../Pages/ErrorPage";
import SignUpPage from "../Pages/SignUpPage";
import DisplayPage from "../Pages/DisplayPage";
import AddPlantPage from "../Pages/AddPlantPage";
import SettingsPage from "../Pages/SettingsPage";
import NavBar from "./NavBar";
import ProtectedRoute from "./ProtectedRoute.tsx";

// Layout component including NavBar - used by both protected and unprotected routes
const MainLayout = () => (
  <>
    <NavBar />
    <Outlet /> {/* Child routes will render here */}
  </>
);

const router = createBrowserRouter([
    {
        path: '/error',
        element: <ErrorPage />,
        errorElement: <ErrorPage />,
    },
    {
        path: '/login',
        element: <LoginPage/>,
    },
    {
        path: '/signup',
        element: <SignUpPage />,
    },
    {
        path: '/display',
        element: <DisplayPage />,
    },
    {
        // Settings route - uses MainLayout but is NOT protected
        path: '/settings',
        element: <MainLayout />,
        children: [
            { index: true, element: <SettingsPage /> }
        ]
    },
    {
        // Protected routes - use ProtectedRoute which includes MainLayout
        path: '/',
        element: <ProtectedRoute />,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true, // HomePage at '/'
                element: <HomePage/>,
            },
            {
                path: 'plant_detail', 
                element: <PlantDetailPage/>,
            },
            {
                path: 'about',
                element: <AboutPage />,
            },
            {
                path: 'faq',
                element: <FaqPage />,
            },
            {
                path: 'add_plant',
                element: <AddPlantPage />
            }
            // Settings is now defined separately above
        ]
    },
]);

function Provider() {
    return (
        <>
            <RouterProvider router={router}/>
        </>
    )
}

export default Provider;