import React, { useCallback, useEffect, useState } from 'react'
import '../Styles/custom/homePage.css'
import PlantCard from '../Components/PlantCard'
import AddNewPlantCard from '../Components/AddNewPlantCard'
import plantController from '../Controller/PlantController'
import { GetPlantData } from '../Interfaces/plantInterface'
import handleApiError, { isAuthTokenInvalid } from '../Utils/apiService'
import { toast } from 'react-toastify'
import { useNavigate } from 'react-router-dom'
import Loader from '../Components/Loader'

function HomePage() {

  const userstring = localStorage.getItem('userDetails');
  const user = userstring ? JSON.parse(userstring): {};
  const [plantData, setPlantData] = useState<Array<GetPlantData>>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadedCount, setLoadedCount] = useState<number>(0);
  const navigate = useNavigate();

  const isLoaded = useCallback(() => {
    setLoadedCount(cnt => cnt+1);
  }, [])

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        const response = await plantController.getPlants();
        setPlantData(response.data);
        toast.success("User's plants fetched successfully", {
          position: 'top-right',
        })
        setLoading(false);
      } catch (error:unknown) {
        if(isAuthTokenInvalid(error)) navigate('/');
        handleApiError(error)
      }
    }
    fetchUserData();
  }, [navigate])

  const allLoaded = loadedCount === plantData.length;

  return (
    <div className='homePage'>
      {(loading || !allLoaded) && <Loader />}
      <div className='nameBar'>{user.firstname || ''}&rsquo;s Plants</div>
      <div className='plantViewer'>
        {
          plantData.map((data, index)=>{
            return <PlantCard key={index} name={data.plantname} sensorId={data.sensorid} deviceId={data.deviceid} isLoaded={isLoaded} />
          })
        }
        <AddNewPlantCard/>
      </div>
    </div>
  )
}

export default HomePage