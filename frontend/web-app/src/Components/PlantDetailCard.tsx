import React from 'react'
import closeBtn from '../Images/plant-card-close-btn-icon.svg'
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
                <img className='plant-detail-card-close-button' src={closeBtn} alt='error img'/>
                <button className='plant-detail-card-edit-button'>Edit</button>
                <button className='plant-detail-card-delete-button'>Delete</button>
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
                            <th>ADC Value</th>
                            <th>Moisture Level</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                        <tr>
                            <td>2/2/2025</td>
                            <td>2:23 pm</td>
                            <td>43243</td>
                            <td>100%</td>
                            <td>Good</td>
                        </tr>
                    </tbody>
                </div>
            </div>
        </div>
    </div>
  )
}

export default PlantDetailCard