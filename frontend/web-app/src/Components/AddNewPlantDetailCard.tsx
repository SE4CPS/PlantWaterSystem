import React, { useEffect, useState } from 'react'
import closeBtn from '../Images/plant-card-close-btn-icon.svg'
import dummyImage from '../Images/rose.png'
import { useNavigate } from 'react-router-dom'
import { AddPlantObject, AddPlantRequestBody, PlantMetaData, SensorTableData } from '../Interfaces/plantInterface';
import handleApiError, { isAuthTokenInvalid } from '../Utils/apiService';
import sensorController from '../Controller/SensorController';
import { toast } from 'react-toastify';
import plantController from '../Controller/PlantController';
import { UserDetails } from '../Interfaces/AuthInterfaces';

function AddNewPlantDetailCard() {

  const navigate = useNavigate();

  const [addPlantObject, setAddPlantObject] = useState<AddPlantObject>({
    name: '',
    sensorId: 'none',
  })

  const [unusedSensorIds, setUnusedSensorIds] = useState<Array<string>>([]);
  const [sensorTableData, setSensorTableData] = useState<Array<SensorTableData>>([]);

  const [userDetails, setUserDetails] = useState<UserDetails>({
    deviceid: '',
    email: '',
    firstname: '',
    lastname: '',
    phonenumber: '',
    userid: -1,
    username: '',
  });

  useEffect(() => {
    const userstring = localStorage.getItem('userDetails');
    const user = userstring? JSON.parse(userstring) : {};
    setUserDetails(user);
  }, [])
  

  const onPlantDetailChange =(key: string, value: string)=>{
    const newObject: AddPlantObject = {
      ...addPlantObject,
      [key]: value
    };

    setAddPlantObject(newObject);
  }

  const fetchSensorData = async (sensorId: string) => {
    try {
        const response = await sensorController.getSensorData(userDetails.deviceid, sensorId);
        setSensorTableData(response.data.data);
    } catch (error: unknown) {
        if(isAuthTokenInvalid(error)) navigate('/');
        handleApiError(error)
    }
  }

  const addNewPlant = async () => {
    if(addPlantObject.name.length<3 && addPlantObject.sensorId==='none'){
        toast.error("Plant Name should be atleast 3 characters or Please assign a sensor to the plant", {
            position: "top-right",
        })
    }
    else{
        try {
            const userstring = localStorage.getItem('userDetails');
            const user = userstring? JSON.parse(userstring):{}
            const body: AddPlantRequestBody = {
                plant_name: addPlantObject.name,
                sensor_id: addPlantObject.sensorId,
                device_id: userDetails.deviceid,
                user_id: `${user.userid}` || '',
            };
            const response = await plantController.addPlant(body);
            toast.success(response.data.message, {
                position: 'top-right',
            });
            const plantMetaData: PlantMetaData = {
                moisture_level: sensorTableData[0].moisture_level,
                deviceId: userDetails.deviceid,
                sensorId: response.data.sensor_id,
                name: response.data.plant_name,
            };
            navigate('/app/plant_detail', {state: plantMetaData});
        } catch (error: unknown) {
            if(isAuthTokenInvalid(error)) navigate('/');
            handleApiError(error)
        }
    }
  }

  useEffect(() => {
    const fetchUnusedSensorIds = async () => {
        if(userDetails.deviceid!==''){
            try {
                const response = await sensorController.getUnusedSensorIDs(userDetails.deviceid);
                const idArray = response.data.sensor_ids || [];
                setUnusedSensorIds(unusedSensorIds => {
                    unusedSensorIds = [...idArray];
                    return unusedSensorIds;
                })
            } catch (error) {
                if(isAuthTokenInvalid(error)) navigate('/');
                handleApiError(error)
            }
        }
    }
    fetchUnusedSensorIds();
  }, [userDetails.deviceid, navigate])

  

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
                        Device ID: <b>{userDetails.deviceid}</b>
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
                            <th>Moisture Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                          sensorTableData.map((data, index) => {
                            return (
                              <tr key={index}>
                                <td>{data.date}</td>
                                <td>{data.time}</td>
                                <td>{data.moisture_level}%</td>
                              </tr>
                            )
                          })
                        }
                    </tbody>
                </div>
            </div>
        </div>
        <div className='add-plant-save-button-container'>
            <button onClick={()=>{addNewPlant()}} className='add-plant-save-button'>Save</button>
        </div>
    </div>
  )
}

export default AddNewPlantDetailCard