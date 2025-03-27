import React from 'react'
import { useNavigate } from 'react-router-dom'

function AddNewPlantCard() {

  const navigate = useNavigate();

  return (
    <div className='addNewPlantCard' onClick={()=>navigate('/add_plant')}>
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