import React, { useEffect, useState } from 'react'
import closeBtn from '../Images/plant-card-close-btn-icon.svg'
import dummyImage from '../Images/rose.png'
import { useNavigate } from 'react-router-dom'
import { AddPlantObject, SensorTableData } from '../Interfaces/plantInterface';
import handleApiError, { isAuthTokenInvalid } from '../Utils/apiService';
import sensorController from '../Controller/SensorController';

function AddNewPlantDetailCard({deviceId}: {deviceId: string}) {

  const navigate = useNavigate();

  const [addPlantObject, setAddPlantObject] = useState<AddPlantObject>({
    name: '',
    sensorId: 'none',
    note: '',
  })

  const [unusedSensorIds, setUnusedSensorIds] = useState<Array<string>>([]);
  const [sensorTableData, setSensorTableData] = useState<Array<SensorTableData>>([]);

  const onPlantDetailChange =(key: string, value: string)=>{
    const newObject: AddPlantObject = {
      ...addPlantObject,
      [key]: value
    };

    setAddPlantObject(newObject);
  }

  const fetchSensorData = async (sensorId: string) => {
    try {
        const response = await sensorController.getSensorData(deviceId, sensorId);
        setSensorTableData(response.data.data);
    } catch (error: unknown) {
        if(isAuthTokenInvalid(error)) navigate('/');
        handleApiError(error)
    }
  }

  useEffect(() => {
    const fetchUnusedSensorIds = async () => {
        try {
            const response = await sensorController.getUnusedSensorIDs(deviceId);
            const idArray = response.data.sensor_ids;
            setUnusedSensorIds(unusedSensorIds => {
                unusedSensorIds = [...idArray];
                return unusedSensorIds;
            })
        } catch (error) {
            if(isAuthTokenInvalid(error)) navigate('/');
            handleApiError(error)
        }
    }
    fetchUnusedSensorIds();
  }, [deviceId, navigate])

  

  return (
    <div className={`plant-detail-card font-poppins Wet`}>
        <div className='plant-detail-card-information'>
            <div className='detail-and-image-container'>
                <img className='plant-detail-card-image' src={dummyImage} alt='error img'/>
                <div className='plant-detail-card-details'>
                    <div>
                        Name: <input type='text' value={addPlantObject.name} onChange={(e)=>{onPlantDetailChange('name', e.target.value)}} />
                    </div>
                    {/* <div>
                        Status: 
                    </div>
                    <div>
                        Last Watered: 
                    </div> */}
                    <div>
                        Sensor ID: <select onChange={(e)=>{
                            onPlantDetailChange('sensorId', e.target.value)
                            if(e.target.value!=='none') fetchSensorData(e.target.value)
                            else setSensorTableData([]);
                            }}>
                            <option selected value={'none'}>Please select an unused sensor ID</option>
                            {
                                unusedSensorIds.map((data, key) => {
                                    return <option value={data} key={key}>{data}</option>
                                })
                            }
                        </select>
                    </div>
                    <div>
                        Device ID: <b>{deviceId}</b>
                    </div>
                    {/* <div>
                        Note: <input type='text' value={addPlantObject.note} onChange={(e)=>{onPlantDetailChange('note', e.target.value)}} />
                    </div> */}
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
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                          sensorTableData.map((data, index) => {
                            return (
                              <tr key={index}>
                                <td>{data.date}</td>
                                <td>{data.time}</td>
                                {/* <td>{data.adcvalue}</td>
                                <td>{data.moisture_level}</td> */}
                                <td>{data.digitalsatus}</td>
                              </tr>
                            )
                          })
                        }
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