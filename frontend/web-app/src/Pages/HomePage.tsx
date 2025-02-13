import React, { useEffect } from 'react'
import authController from '../Controller/AuthController'

function HomePage() {
// example of using APIs
// you need not necessarily call APIs in useEffect
// you may also call them through other ways 
// but make sure to keep them in async functions 
// and use await while calling them to resolve Promise.

  useEffect(() => {
    const fetchUserData = async () => {
      const data = await authController.getUsers();
      console.log(data);
    }
    fetchUserData();
  }, [])

  return (
    <div>HomePage</div>
  )
}

export default HomePage 