import React from 'react'
import '../Styles/custom/plantDetailPage.css'
import PlantDetailCard from '../Components/PlantDetailCard'

function PlantDetailPage() {
  return (
    <div className='plant-detail-page'>
      <PlantDetailCard status='good' />
    </div>
  )
}

export default PlantDetailPage