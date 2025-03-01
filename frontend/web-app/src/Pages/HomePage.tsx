import React, { useEffect, useState } from 'react'
import '../Styles/custom/homePage.css'
import PlantCard from '../Components/PlantCard'
import AddNewPlantCard from '../Components/AddNewPlantCard'
import plantController from '../Controller/PlantController'
import { GetPlantData } from '../Interfaces/plantInterface'

function HomePage() {

  const [plantData, setPlantData] = useState<Array<GetPlantData>>([]);

  useEffect(() => {
    const fetchUserData = async () => {
      const response = await plantController.getPlants();
      setPlantData(response.data);
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