import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import LoginPage from "../Pages/LoginPage";
import HomePage from "../Pages/HomePage";
import PlantDetailPage from "../Pages/PlantDetailPage";
import AboutPage from "../Pages/AboutPage";
import FaqPage from "../Pages/FaqPage";
import ErrorPage from "../Pages/ErrorPage";
import NavBar from "./NavBar";
import SignUpPage from "../Pages/SignUpPage";
import DisplayPage from "../Pages/DisplayPage";
import SettingsPage from "../Pages/SettingsPage";

const router = createBrowserRouter([
    {
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
        path: '/',
        element: <NavBar />,
        children: [
            {
                path: '/',
                element: <HomePage/>,
            },
            {
                path: '/plant_detail',
                element: <PlantDetailPage/>,
            },
            {
                path: '/about',
                element: <AboutPage />,
            },
            {
                path: '/faq',
                element: <FaqPage />,
            },
            {
                path: '/display',
                element: <DisplayPage />
            },
            {
                path: '/settings',
                element: <SettingsPage />
            }
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