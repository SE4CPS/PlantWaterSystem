import React, { useEffect, useState } from 'react'
import '../Styles/custom/plantCard.css'
import { useNavigate } from 'react-router-dom'
import plantController from '../Controller/PlantController';
import handleApiError, { isAuthTokenInvalid } from '../Utils/apiService';
import sproutlyLogo from '../Images/sproutly-logo.svg';
import { PlantMetaData } from '../Interfaces/plantInterface';
// import dummyImage from '../Images/rose.png'

const imageMap = new Map<string, string>([
  ['Tulip', 'https://www.colorblends.com/wp-content/uploads/2020/01/1504_BestPurple_CGC2662sq-1024x1024.jpg'],
  ['Rose', 'https://luukminkman.com/media/filer_public_thumbnails/blog_posts/216/images/How%20to%20draw%20a%20rose%20reference%20photo.jpg__1000x1000_q85_subsampling-2.jpg'],
  ['orchids', 'https://hips.hearstapps.com/hmg-prod/images/phalaenopsis-orchid-moth-orchid-types-1587739487.jpg?crop=1.00xw:1.00xh;0,0&resize=980:*'],
  ['Sunflower', 'https://images.unsplash.com/photo-1597848212624-a19eb35e2651?q=80&w=1935&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D']
])

function PlantCard({name, sensorId, deviceId, isLoaded}: {name: string, sensorId: string, deviceId: string, isLoaded: ()=>void}) {

  const navigate = useNavigate();
  const [plantMetaData, setPlantMetaData] = useState<PlantMetaData>({moisture_level: 0, name, sensorId, deviceId});
  const [status, setStatus] = useState(0);

  useEffect(() => {
    const fetchPlantStatus= async ()=>{
      try {
        const response = await plantController.getPlantStatus(sensorId, deviceId);
        const curr_status = response.data.moisture_level;
        setStatus(curr_status)
        setPlantMetaData(plantMetaData => {
          plantMetaData.moisture_level = curr_status;
          return plantMetaData
        })
        isLoaded();
      } catch (error: unknown) {
        if(isAuthTokenInvalid(error)) navigate('/');
        handleApiError(error)
      }
    }
    fetchPlantStatus();
  }, [sensorId, deviceId, navigate, isLoaded])
  
  return (
    <div className={`plantCard ${status > 25? 'Wet' : 'Dry'}`} onClick={()=>navigate('/app/plant_detail', { state: plantMetaData })}>
      {status < 25? <div className='plantCard-dry-status-indicator'><b>Water Me!</b></div> : null}
      <img className='plantCard-image' src={imageMap.get(name) || sproutlyLogo} alt='Error img'/>
      <div className='plantCard-detail'>
        <div>
          Name: <b>{name}</b>
        </div>
        <div>
          Moisture Level: <b>{status}%</b>
        </div>
      </div>
    </div>
  )
}

export default PlantCard