import React from 'react'
import '../Styles/custom/plantCard.css'
import dummyImage from '../Images/rose.png'

function PlantCard({status}: {status: string}) {
  return (
    <div className={`plantCard ${status}`}>
      {status==='dry'? <div className='plantCard-dry-status-indicator'><b>Water Me!</b></div> : null}
      <img className='plantCard-image' src={dummyImage} alt='Error Img'/>
      <div className='plantCard-detail'>
        <div>
          Name: <b>Red Rose</b>
        </div>
        <div>
          Status: <b>Good</b>
        </div>
        <div>
          Last Watered: <b>3:15 pm</b> on <b>2/6/2025</b>
        </div>
      </div>
    </div>
  )
}

export default PlantCard