import React from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Copy, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'
import { useTranslation } from '../hooks/useTranslation'
import './SuccessMessage.css'

const SuccessMessage = ({ complaint, onReset }) => {
  const navigate = useNavigate()
  const { t, getStatusTranslation, getUrgencyTranslation } = useTranslation()

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    alert(t('successCopied'))
  }

  const handleCheckStatus = () => {
    navigate(`/status/${complaint.id}`)
  }

  return (
    <div className="success-message">
      <div className="success-icon">
        <CheckCircle size={64} color="#10b981" />
      </div>
      <h1>{t('successTitle')}</h1>
      <p className="success-description">
        {t('successDescription')}
      </p>

      <div className="complaint-details">
        <div className="detail-item">
          <span className="detail-label">{t('successComplaintId')}</span>
          <div className="detail-value">
            <code>{complaint.id}</code>
            <button 
              className="icon-button" 
              onClick={() => copyToClipboard(complaint.id)}
              title="Copy ID"
            >
              <Copy size={16} />
            </button>
          </div>
        </div>

        <div className="detail-item">
          <span className="detail-label">{t('successStatus')}</span>
          <span className={`status-badge status-${complaint.status}`}>
            {getStatusTranslation(complaint.status)}
          </span>
        </div>

        <div className="detail-item">
          <span className="detail-label">{t('successDepartment')}</span>
          <span className="detail-value">{complaint.assigned_department}</span>
        </div>

        <div className="detail-item">
          <span className="detail-label">{t('successUrgency')}</span>
          <span className={`urgency-badge urgency-${complaint.urgency}`}>
            {getUrgencyTranslation(complaint.urgency)}
          </span>
        </div>

        <div className="detail-item">
          <span className="detail-label">{t('successResolution')}</span>
          <span className="detail-value">
            {format(new Date(complaint.sla_deadline), 'PPpp')}
          </span>
        </div>

        <div className="detail-item">
          <span className="detail-label">{t('successSubmitted')}</span>
          <span className="detail-value">
            {format(new Date(complaint.created_at), 'PPpp')}
          </span>
        </div>
      </div>

      <div className="success-actions">
        <button className="btn btn-primary" onClick={handleCheckStatus}>
          <ExternalLink size={18} />
          <span>{t('successCheckStatus')}</span>
        </button>
        <button className="btn btn-secondary" onClick={onReset}>
          {t('successAnother')}
        </button>
      </div>

      <div className="notification-info">
        <p>{t('successNotification')}</p>
        <p>{t('successSaveId')}</p>
      </div>
    </div>
  )
}

export default SuccessMessage

