import React from 'react'
import '../Styles/custom/aboutPage.css'

function AboutPage() {
  return (
    <div className='font-poppins about-container'>
      <h1>What is Sproutly?</h1>
      <p>🌱 Sproutly helps you take care of your plants by tracking watering times and sending you reminders. Sproutly is a perfect tool for plant lovers or beginners! ✨</p>
      <h1>How can I use Sproutly?</h1>
      <div className="bullet-container">
        <div className="bullet">
          <div className="bullet-number">
            <h2>1</h2>
          </div>
          <div className="bullet-text">
            <h2 className="bullet-title">Add your plants</h2>
            <p>Click on the &quot;+&quot; button on the home screen to add a new plant.</p>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>2</h2>
          </div>
          <div className="bullet-text">
            <h2 className="bullet-title">Track watering & moisture levels</h2>
            <p>Each plant has a detailed history with moisture data.</p>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>3</h2>
          </div>
          <div className="bullet-text">
            <h2 className="bullet-title">Get reminders</h2>
            <p className="bullet-description">Sproutly will send you an email notification you when your plant needs water!</p>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>4</h2>
          </div>
          <div className="bullet-text">
            <h2 className="bullet-title">Monitor plant health</h2>
            <p>Check if your plant is in &quot;Good&quot; or &quot;Dry&quot; condition.</p>
          </div>
        </div>
      </div>
      <h1>Why use Sproutly?</h1>
      <div className="bullet-container">
  
        <div className="bullet">
          <div className="bullet-number">
            <h2>✓</h2>
          </div>
          <div className="bullet-text">
            <h2 className="why-bullet-title">Never forget to water your plants</h2>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>✓</h2>
          </div>
          <div className="bullet-text">
            <h2 className="why-bullet-title">Easy-to-use interface</h2>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>✓</h2>
          </div>
          <div className="bullet-text">
            <h2 className="why-bullet-title">Personalized plant tracking</h2>
          </div>
        </div>

        <div className="bullet">
          <div className="bullet-number">
            <h2>✓</h2>
          </div>
          <div className="bullet-text">
            <h2 className="why-bullet-title">Perfect for beginners</h2>
          </div>
        </div>
      </div>
      <h1>Need help?</h1>
      <p>📌 Check our <span className="faq-link">FAQ page</span> for common questions!</p>
      <p>📩 Contact us if you need support.</p>
    </div>
  )
}

export default AboutPage