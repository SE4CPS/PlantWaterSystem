import React from 'react'
import { useNavigate } from 'react-router-dom'

function AddNewPlantCard({deviceId}: {deviceId: string}) {

  const navigate = useNavigate();

  return (
    <div className='addNewPlantCard' onClick={()=>navigate('/app/add_plant', {state: {deviceId}})}>
        <div className='addNewPlantCard-text'>
            Add a new plant
        </div>
        <div className='addNewPlantCard-icon'>
            +
        </div>
    </div>
  )
}

export default AddNewPlantCard