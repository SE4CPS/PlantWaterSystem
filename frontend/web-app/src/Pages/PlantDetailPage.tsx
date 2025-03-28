import React from 'react'
import '../Styles/custom/plantDetailPage.css'
import PlantDetailCard from '../Components/PlantDetailCard'
import { useLocation } from 'react-router-dom'

function PlantDetailPage() {

  const location = useLocation();
  const plantMetaData = location.state;

  return (
    <div className='plant-detail-page'>
      <PlantDetailCard status='good' plantMetaData={plantMetaData} />
    </div>
  )
}

export default PlantDetailPage