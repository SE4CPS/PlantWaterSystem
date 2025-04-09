import React, { useState } from 'react'
import closeBtn from '../Images/plant-card-close-btn-icon.svg'
import dummyImage from '../Images/rose.png'
import { useNavigate } from 'react-router-dom'
import { AddPlantObject } from '../Interfaces/plantInterface';

function AddNewPlantDetailCard() {

  const navigate = useNavigate();

  const [addPlantObject, setAddPlantObject] = useState<AddPlantObject>({
    name: '',
    sensorId: '',
    note: '',
  })

  const onPlantDetailChange =(key: string, value: string)=>{
    const newObject: AddPlantObject = {
      ...addPlantObject,
      [key]: value
    };

    setAddPlantObject(newObject);
  }

  return (
    <div className={`plant-detail-card font-poppins Wet`}>
        <div className='plant-detail-card-information'>
            <div className='detail-and-image-container'>
                <img className='plant-detail-card-image' src={dummyImage} alt='error img'/>
                <div className='plant-detail-card-details'>
                    <div>
                        Name: <input type='text' value={addPlantObject.name} onChange={(e)=>{onPlantDetailChange('name', e.target.value)}} />
                    </div>
                    <div>
                        Status: 
                    </div>
                    <div>
                        Last Watered: 
                    </div>
                    <div>
                        Sensor ID: <input type='text' value={addPlantObject.sensorId} onChange={(e)=>{onPlantDetailChange('sensorId', e.target.value)}} /> 
                    </div>
                    <div>
                        Device ID: <b>1234</b>
                    </div>
                    <div>
                        Note: <input type='text' value={addPlantObject.note} onChange={(e)=>{onPlantDetailChange('note', e.target.value)}} />
                    </div>
                </div>
            </div>
            <div className='plant-detail-card-button-container' onClick={()=>{navigate('/app/dashboard')}}>
                <img className='plant-detail-card-close-button' src={closeBtn} alt='error img'/>
            </div>
        </div>
        <div className='plant-detail-card-history'>
            <div className='title'>
                Water History
            </div>
            <div className='history-table-container'>
                <div className='history-table'>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>ADC Value</th>
                            <th>Moisture Level</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                    </tbody>
                </div>
            </div>
        </div>
        <div className='add-plant-save-button-container'>
            <button className='add-plant-save-button'>Save</button>
        </div>
    </div>
  )
}

export default AddNewPlantDetailCard