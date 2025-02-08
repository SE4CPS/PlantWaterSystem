import { createBrowserRouter, RouterProvider } from "react-router-dom";
import LoginPage from "../Pages/LoginPage";
import HomePage from "../Pages/HomePage";
import PlantDetailPage from "../Pages/PlantDetailPage";
import AboutPage from "../Pages/AboutPage";
import FaqPage from "../Pages/FaqPage";
import ErrorPage from "../Pages/ErrorPage";

const router = createBrowserRouter([
    {
        errorElement: <ErrorPage />,
    },
    {
        path: '/login',
        element: <LoginPage/>,
    },
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
]);

function Provider() {
    return (
        <>
            <RouterProvider router={router}/>
        </>
    )
}

export default Provider;