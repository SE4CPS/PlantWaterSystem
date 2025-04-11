import React from 'react'
import '../Styles/custom/faqPage.css'

function FaqPage() {
  return (
    <div className='font-poppins about-container'>
      <h1>Frequently Asked Questions (FAQs)</h1>
      <p>🌿 Got questions? We've got answers! 🌿</p>
      <div className='question-container'>
        <div className='question'>
          <h2>Is Sproutly free?</h2>
          <p>Yes! Sproutly is completely free to use.</p>
        </div>

        <div className='question'>
          <h2>How will I know when to water my plant?</h2>
          <p>When your plant is dry, Sproutly will send you a notification through your preferred method of communication.</p>
        </div>

        <div className='question'>
          <h2>Can I track multiple plants?</h2>
          <p>Yes! You can add and manage as many plants as you like.</p>
        </div>

        <div className='question'>
          <h2>Does Sproutly work for all types of plants?</h2>
          <p>Sproutly is currently designed for indoor plants due to the use of sensor devices.</p>
        </div>

      </div>
    </div>
  )
}

export default FaqPage