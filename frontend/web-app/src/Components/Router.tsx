import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import LoginPage from "../Pages/LoginPage";
import HomePage from "../Pages/HomePage";
import PlantDetailPage from "../Pages/PlantDetailPage";
import AboutPage from "../Pages/AboutPage";
import FaqPage from "../Pages/FaqPage";
import ErrorPage from "../Pages/ErrorPage";
import NavBar from "./NavBar";
import DisplayPage from "../Pages/DisplayPage";
import AddPlantPage from "../Pages/AddPlantPage";
import SettingsPage from "../Pages/SettingsPage";

const router = createBrowserRouter([
    {
        errorElement: <ErrorPage />,
    },
    {
        path: '/',
        element: <LoginPage/>,
    },
    {
        path: '/display',
        element: <NavBar />,
        children: [
            {
                path: '',
                element: <DisplayPage />
            }
        ],
    },
    {
        path: '/app',
        element: <NavBar />,
        children: [
            {
                path: 'dashboard',
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
            },
            {
                path: 'settings',
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