import React from 'react';
import RouterProvider from './Components/Router';
import './Styles/global.css'
import 'react-toastify/dist/ReactToastify.css'
import { ToastContainer } from 'react-toastify';

function App() {
  return (
    <div className="App">
      <RouterProvider />
      <ToastContainer />
    </div>
  );
}

export default App;
