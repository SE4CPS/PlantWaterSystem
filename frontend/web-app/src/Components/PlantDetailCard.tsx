import React, { useEffect, useState } from 'react'
import closeBtn from '../Images/plant-card-close-btn-icon.svg'
import dummyImage from '../Images/rose.png'
import { PlantMetaData, SensorTableData } from '../Interfaces/plantInterface'
import { useNavigate } from 'react-router-dom'
import sensorController from '../Controller/SensorController'
import handleApiError, { isAuthTokenInvalid } from '../Utils/apiService'

function PlantDetailCard({status, plantMetaData}: {status: string, plantMetaData: PlantMetaData}) {

  const navigate = useNavigate();

  const [sensorTableData, setSensorTableData] = useState<Array<SensorTableData>>([]);

  useEffect(() => {
    const fetchSensorTableData = async () => {
      try {
        const response = await sensorController.getSensorData();
        setSensorTableData(response.data.data);
      } catch (error) {
        if(isAuthTokenInvalid(error)) navigate('/')
        handleApiError(error);
      }
    }
    fetchSensorTableData();
  }, [navigate])
  

  return (
    <div className={`plant-detail-card font-poppins ${status}`}>
        <div className='plant-detail-card-information'>
            <div className='detail-and-image-container'>
                <img className='plant-detail-card-image' src={dummyImage} alt='error img'/>
                <div className='plant-detail-card-details'>
                    <div>
                        Name: <b>{plantMetaData.name}</b>
                    </div>
                    <div>
                        Status: <b>Good</b>
                    </div>
                    <div>
                        Last Watered: <b>3:15pm</b> on <b>2/6/2025</b>
                    </div>
                    <div>
                        Sensor ID: <b>{plantMetaData.sensorId}</b>
                    </div>
                    <div>
                        Device ID: <b>{plantMetaData.deviceId}</b>
                    </div>
                    <div>
                        Note: <b>Place this plant near the window</b>
                    </div>
                </div>
            </div>
            <div className='plant-detail-card-button-container'>
                <img className='plant-detail-card-close-button' src={closeBtn} alt='error img' onClick={()=>navigate('/')}/>
                <button className='plant-detail-card-edit-button'>Edit</button>
                <button className='plant-detail-card-delete-button'>Delete</button>
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
                        {
                          sensorTableData.map((data, index) => {
                            return (
                              <tr key={index}>
                                <td>{data.date}</td>
                                <td>{data.time}</td>
                                <td>{data.adcvalue}</td>
                                <td>{data.moisture_level}</td>
                                <td>{data.digitalsatus}</td>
                              </tr>
                            )
                          })
                        }
                    </tbody>
                </div>
            </div>
        </div>
    </div>
  )
}

export default PlantDetailCard