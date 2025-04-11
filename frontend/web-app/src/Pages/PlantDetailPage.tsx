import React from 'react'
import '../Styles/custom/plantDetailPage.css'
import PlantDetailCard from '../Components/PlantDetailCard'
import { useLocation } from 'react-router-dom'
import { PlantMetaData } from '../Interfaces/plantInterface';

function PlantDetailPage() {

  const location = useLocation();
  const plantMetaData: PlantMetaData = location.state || {status: '', name: '', deviceId: '', sensorId: ''};

  return (
    <div className='plant-detail-page'>
      <PlantDetailCard plantMetaData={plantMetaData} />
    </div>
  )
}

export default PlantDetailPage