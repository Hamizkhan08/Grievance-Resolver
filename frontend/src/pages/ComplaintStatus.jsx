import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Loader2, Search, Clock, Building2, AlertCircle, MessageCircle } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import Chatbot from '../components/Chatbot'
import { useTranslation } from '../hooks/useTranslation'
import VoiceInput from '../components/VoiceInput'
import './ComplaintStatus.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const ComplaintStatus = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t, getStatusTranslation, getUrgencyTranslation } = useTranslation()
  const [complaintId, setComplaintId] = useState(id || '')
  const [complaint, setComplaint] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (id) {
      fetchComplaintStatus(id)
    }
  }, [id])

  const fetchComplaintStatus = async (cid) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_BASE_URL}/api/complaints/${cid}`)
      if (response.data.success) {
        setComplaint(response.data.complaint)
      } else {
        setError(response.data.error || t('statusNotFound'))
      }
    } catch (err) {
      setError(
        err.response?.data?.error ||
        err.message ||
        t('statusFetchError')
      )
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    if (complaintId.trim()) {
      fetchComplaintStatus(complaintId.trim())
    }
  }

  const handleVoiceTranscript = (transcript) => {
    // Clean transcript and set as complaint ID
    const cleaned = transcript.trim().replace(/\s+/g, '')
    setComplaintId(cleaned)
    // Auto-search after a short delay
    setTimeout(() => {
      if (cleaned) {
        fetchComplaintStatus(cleaned)
      }
    }, 500)
  }

  const getStatusColor = (status) => {
    const colors = {
      open: '#3b82f6',
      in_progress: '#f59e0b',
      escalated: '#ef4444',
      resolved: '#10b981',
      closed: '#6b7280',
    }
    return colors[status] || '#6b7280'
  }

  const getTimeRemainingColor = (hours) => {
    if (hours < 0) return '#ef4444' // Overdue
    if (hours < 24) return '#f59e0b' // Urgent
    return '#10b981' // Good
  }

  return (
    <div className="complaint-status">
      <div className="status-header">
        <h1>{t('statusTitle')}</h1>
        <p>{t('statusSubtitle')}</p>
      </div>

      <div className="search-section">
        <div className="search-box">
          <Search size={20} />
          <div className="search-input-wrapper">
            <input
              type="text"
              placeholder={t('statusPlaceholder')}
              value={complaintId}
              onChange={(e) => setComplaintId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <VoiceInput 
              onTranscript={handleVoiceTranscript}
              disabled={loading}
            />
          </div>
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? <Loader2 className="spinner" /> : t('statusSearch')}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-card">
          <AlertCircle size={24} />
          <div>
            <h3>{t('statusError')}</h3>
            <p>{error}</p>
          </div>
        </div>
      )}

      {complaint && (
        <div className="status-card">
          <div className="status-header-section">
            <div>
              <h2>{t('statusComplaintId')}{complaint.id.slice(0, 8)}</h2>
              <p className="complaint-description">{complaint.description}</p>
            </div>
            <div
              className="status-badge-large"
              style={{ backgroundColor: getStatusColor(complaint.status) + '20', color: getStatusColor(complaint.status) }}
            >
              {getStatusTranslation(complaint.status)}
            </div>
          </div>

          <div className="status-details">
            <div className="detail-card">
              <Building2 size={20} />
              <div>
                <span className="detail-label">{t('statusDepartment')}</span>
                <span className="detail-value">{complaint.current_department}</span>
              </div>
            </div>

            <div className="detail-card">
              <Clock size={20} />
              <div>
                <span className="detail-label">{t('statusTimeRemaining')}</span>
                <span
                  className="detail-value"
                  style={{ color: getTimeRemainingColor(complaint.time_remaining_hours) }}
                >
                  {complaint.time_remaining_hours !== null
                    ? complaint.time_remaining_hours > 0
                      ? `${Math.floor(complaint.time_remaining_hours / 24)} ${t('days')}, ${Math.floor(complaint.time_remaining_hours % 24)} ${t('hours')}`
                      : t('statusOverdue')
                    : t('statusNA')}
                </span>
              </div>
            </div>

            <div className="detail-card">
              <span className="detail-label">{t('statusUrgency')}</span>
              <span className={`urgency-badge urgency-${complaint.urgency}`}>
                {getUrgencyTranslation(complaint.urgency)}
              </span>
            </div>

            {complaint.escalation_level !== 'none' && (
              <div className="detail-card escalation-notice">
                <AlertCircle size={20} />
                <div>
                  <span className="detail-label">{t('statusEscalation')}</span>
                  <span className="detail-value">{complaint.escalation_level.replace('_', ' ').toUpperCase()}</span>
                </div>
              </div>
            )}

            <div className="detail-card">
              <span className="detail-label">{t('statusLastUpdated')}</span>
              <span className="detail-value">
                {format(new Date(complaint.last_update), 'PPpp')}
                <br />
                <small style={{ color: 'var(--text-secondary)' }}>
                  {formatDistanceToNow(new Date(complaint.last_update), { addSuffix: true })}
                </small>
              </span>
            </div>
          </div>

          <div className="notification-section">
            <p>{t('statusNotification')}</p>
          </div>

          {/* Forum Link */}
          <div className="forum-link-section">
            <a href={`/forum/${complaint.id}`} className="forum-link">
              <MessageCircle size={20} />
              <div>
                <h3>{t('discussComplaint') || 'Discuss & Vote'}</h3>
                <p>{t('forumLinkDescription') || 'Share your experience or vote if you have a similar incident'}</p>
              </div>
            </a>
          </div>
        </div>
      )}

      {complaint && (
        <Chatbot 
          complaintId={complaint.id}
          citizenEmail={complaint.citizen_email}
        />
      )}
    </div>
  )
}

export default ComplaintStatus

