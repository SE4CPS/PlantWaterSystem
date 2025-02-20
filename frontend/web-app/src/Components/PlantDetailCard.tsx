import React from 'react'
import dummyImage from '../Images/rose.png'

function PlantDetailCard({status}: {status: string}) {
  return (
    <div className={`plant-detail-card font-poppins ${status}`}>
        <div className='plant-detail-card-information'>
            <div className='detail-and-image-container'>
                <img className='plant-detail-card-image' src={dummyImage} alt='error img'/>
                <div className='plant-detail-card-details'>
                    <div>
                        Name: <b>Red Rose</b>
                    </div>
                    <div>
                        Status: <b>Good</b>
                    </div>
                    <div>
                        Last Watered: <b>3:15pm</b> on <b>2/6/2025</b>
                    </div>
                    <div>
                        Note: <b>Place this plant near the window</b>
                    </div>
                </div>
            </div>
            <div className='plant-detail-card-button-container'>
                <img className='plant-detail-card-close-button' src='' alt='error img'/>
                <button className='plant-detail-card-edit-button'>Edit</button>
                <button className='plant-detail-card-delete-button'>Delete</button>
            </div>
        </div>
        <div className='plant-detail-card-history'>

        </div>
    </div>
  )
}

export default PlantDetailCard