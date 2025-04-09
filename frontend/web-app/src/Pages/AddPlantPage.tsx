import React from 'react'
import AddNewPlantDetailCard from '../Components/AddNewPlantDetailCard'
import { useLocation } from 'react-router-dom'

function AddPlantPage() {
  const location = useLocation();

  return (
    <div className='plant-detail-page'>
      <AddNewPlantDetailCard deviceId = {location.state.deviceId}/>
    </div>
  )
}

export default AddPlantPage