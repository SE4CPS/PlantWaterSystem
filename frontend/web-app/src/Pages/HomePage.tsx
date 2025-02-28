import React, { useEffect, useState } from 'react'
import '../Styles/custom/homePage.css'
import PlantCard from '../Components/PlantCard'
import AddNewPlantCard from '../Components/AddNewPlantCard'
import plantController from '../Controller/PlantController'
import { GetPlantData } from '../Interfaces/plantInterface'
import handleApiError from '../Utils/apiService'
import { toast } from 'react-toastify'

function HomePage() {

  const [plantData, setPlantData] = useState<Array<GetPlantData>>([]);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await plantController.getPlants();
        setPlantData(response.data);
        toast.success("User's plants fetched successfully", {
          position: 'top-right',
        })
      } catch (error:unknown) {
        handleApiError(error)
      }
    }
    fetchUserData();
  }, [])

  return (
    <div className='homePage'>
      <div className='nameBar'>Vy&rsquo;s Plants</div>
      <div className='plantViewer'>
        {
          plantData.map((data, index)=>{
            return <PlantCard key={index} status='good' name={data.PlantName} />
          })
        }
        <AddNewPlantCard />
      </div>
    </div>
  )
}

export default HomePage