import { createBrowserRouter, RouterProvider } from "react-router-dom";
import LoginPage from "../Pages/LoginPage";
import HomePage from "../Pages/HomePage";
import PlantDetailPage from "../Pages/PlantDetailPage";
import AboutPage from "../Pages/AboutPage";
import FaqPage from "../Pages/FaqPage";
import ErrorPage from "../Pages/ErrorPage";
<<<<<<< HEAD
=======
import NavBar from "./NavBar";
import SignUpPage from "../Pages/SignUpPage";
import DisplayPage from "../Pages/DisplayPage";
>>>>>>> fe68087a11103b291e8a14f454bdff774de1db60

const router = createBrowserRouter([
    {
        errorElement: <ErrorPage />,
    },
    {
        path: '/login',
        element: <LoginPage/>,
    },
    {
<<<<<<< HEAD
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
=======
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
>>>>>>> fe68087a11103b291e8a14f454bdff774de1db60
]);

function Provider() {
    return (
        <>
            <RouterProvider router={router}/>
        </>
    )
}

export default Provider;