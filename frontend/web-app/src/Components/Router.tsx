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
        path: '/display',
        element: <DisplayPage />
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