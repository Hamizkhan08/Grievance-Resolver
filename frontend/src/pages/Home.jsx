import React, { useState } from 'react'
import ComplaintForm from '../components/ComplaintForm'
import MapPicker from '../components/MapPicker'
import SuccessMessage from '../components/SuccessMessage'
import { useTranslation } from '../hooks/useTranslation'
import './Home.css'

const Home = () => {
  const [submittedComplaint, setSubmittedComplaint] = useState(null)
  const { t } = useTranslation()

  const handleSuccess = (complaint) => {
    setSubmittedComplaint(complaint)
  }

  const handleReset = () => {
    setSubmittedComplaint(null)
  }

  if (submittedComplaint) {
    return (
      <SuccessMessage 
        complaint={submittedComplaint} 
        onReset={handleReset}
      />
    )
  }

  return (
    <div className="home">
      <div className="home-header">
        <h1>{t('homeTitle')}</h1>
        <p className="subtitle">
          {t('homeSubtitle')}
        </p>
      </div>
      <div className="home-content">
        <div className="form-section">
          <ComplaintForm onSuccess={handleSuccess} />
        </div>
        <div className="map-section">
          <MapPicker onLocationSelect={(loc) => console.log('Location selected:', loc)} />
        </div>
      </div>
    </div>
  )
}

export default Home

