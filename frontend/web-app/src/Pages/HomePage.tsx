import React, { useEffect } from 'react'
import authController from '../Controller/AuthController'
import '../Styles/custom/homePage.css'
import PlantCard from '../Components/PlantCard'
import AddNewPlantCard from '../Components/AddNewPlantCard'

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
    <div className='homePage'>
      <div className='nameBar'>Vy&rsquo;s Plants</div>
      <div className='plantViewer'>
        <PlantCard status='dry'/>
        <PlantCard status='good'/>
        <PlantCard status='dry'/>
        <PlantCard status='good'/>
        <PlantCard status='good'/>
        <PlantCard status='dry'/>
        <PlantCard status='good'/>
        <AddNewPlantCard />
      </div>
    </div>
  )
}

export default HomePage