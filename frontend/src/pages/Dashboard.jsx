import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle, RefreshCw, Filter, Edit2, Mail } from 'lucide-react'
import { useTranslation } from '../hooks/useTranslation'
import './Dashboard.css'
import { API_URL as API_BASE_URL } from '../lib/config'

const Dashboard = () => {
  const { t, getStatusTranslation, getUrgencyTranslation } = useTranslation()
  const [metrics, setMetrics] = useState(null)
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [complaintsLoading, setComplaintsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showComplaints, setShowComplaints] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [departmentFilter, setDepartmentFilter] = useState('all')
  const [editingStatus, setEditingStatus] = useState(null)
  const [statusNotes, setStatusNotes] = useState('')
  const [updatingStatus, setUpdatingStatus] = useState(null)

  useEffect(() => {
    fetchMetrics()
    fetchComplaints()
  }, [statusFilter, departmentFilter])

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/dashboard`)
      if (response.data.success) {
        setMetrics(response.data.metrics)
      }
    } catch (err) {
      setError(t('dashboardError') || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const fetchComplaints = async () => {
    setComplaintsLoading(true)
    try {
      const params = {}
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      if (departmentFilter !== 'all') {
        params.department = departmentFilter
      }
      
      const response = await axios.get(`${API_BASE_URL}/api/admin/complaints`, { params })
      if (response.data.success) {
        setComplaints(response.data.complaints || [])
      }
    } catch (err) {
      console.error('Failed to fetch complaints:', err)
    } finally {
      setComplaintsLoading(false)
    }
  }

  const handleStatusChange = async (complaintId, newStatus) => {
    if (!newStatus) return
    
    setUpdatingStatus(complaintId)
    try {
      const params = { new_status: newStatus }
      if (statusNotes.trim()) {
        params.notes = statusNotes.trim()
      }
      
      const response = await axios.patch(
        `${API_BASE_URL}/api/admin/complaints/${complaintId}/status`,
        null,
        { params }
      )
      
      if (response.data.success) {
        // Refresh complaints and metrics
        await fetchComplaints()
        await fetchMetrics()
        setEditingStatus(null)
        setStatusNotes('')
        alert(t('statusUpdatedSuccess') || 'Status updated successfully! Email notification sent.')
      } else {
        alert(response.data.error || t('statusUpdateFailed') || 'Failed to update status')
      }
    } catch (err) {
      alert(err.response?.data?.error || err.message || t('statusUpdateFailed') || 'Failed to update status')
      console.error('Status update error:', err)
    } finally {
      setUpdatingStatus(null)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return dateString
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      open: '#2196f3',
      in_progress: '#ff9800',
      resolved: '#4caf50',
      escalated: '#f44336',
      closed: '#9e9e9e'
    }
    return colors[status] || colors.open
  }

  const getUrgencyColor = (urgency) => {
    const colors = {
      urgent: '#f44336',
      high: '#ff9800',
      medium: '#2196f3',
      low: '#4caf50'
    }
    return colors[urgency] || colors.medium
  }

  const statusOptions = [
    { value: 'open', label: t('statusOpen') || 'Open' },
    { value: 'in_progress', label: t('statusInProgress') || 'In Progress' },
    { value: 'resolved', label: t('statusResolved') || 'Resolved' },
    { value: 'escalated', label: t('statusEscalated') || 'Escalated' },
    { value: 'closed', label: t('statusClosed') || 'Closed' }
  ]

  // Get unique departments for filter
  const departments = [...new Set(complaints.map(c => c.responsible_department).filter(Boolean))]

  if (loading) {
    return <div className="dashboard-loading">{t('dashboardLoading') || 'Loading dashboard...'}</div>
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>{t('dashboardTitle') || 'Admin Dashboard'}</h1>
          <p>{t('dashboardSubtitle') || 'Manage and monitor all complaints'}</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => {
            fetchMetrics()
            fetchComplaints()
          }}
        >
          <RefreshCw size={18} />
          {t('refresh') || 'Refresh'}
        </button>
      </div>

      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon">
              <BarChart3 size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardTotal') || 'Total Complaints'}</span>
              <span className="metric-value">{metrics.total_complaints}</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon open">
              <TrendingUp size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardOpen') || 'Open'}</span>
              <span className="metric-value">{metrics.by_status.open}</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon in-progress">
              <TrendingUp size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardInProgress') || 'In Progress'}</span>
              <span className="metric-value">{metrics.by_status.in_progress}</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon resolved">
              <CheckCircle size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardResolved') || 'Resolved'}</span>
              <span className="metric-value">{metrics.by_status.resolved}</span>
            </div>
          </div>

          <div className="metric-card escalated">
            <div className="metric-icon">
              <AlertTriangle size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardEscalated') || 'Escalated'}</span>
              <span className="metric-value">{metrics.by_status.escalated}</span>
            </div>
          </div>

          <div className="metric-card sla-breach">
            <div className="metric-icon">
              <AlertTriangle size={24} />
            </div>
            <div className="metric-content">
              <span className="metric-label">{t('dashboardSLABreach') || 'SLA Breaches'}</span>
              <span className="metric-value">{metrics.sla_breaches}</span>
            </div>
          </div>
        </div>
      )}

      {metrics?.by_department && (
        <div className="department-breakdown">
          <h2>{t('dashboardByDepartment') || 'By Department'}</h2>
          <div className="department-list">
            {Object.entries(metrics.by_department).map(([dept, count]) => (
              <div key={dept} className="department-item">
                <span className="department-name">{dept}</span>
                <span className="department-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="complaints-section">
        <div className="complaints-header">
          <h2>{t('allComplaints') || 'All Complaints'}</h2>
          <div className="filters">
            <div className="filter-group">
              <Filter size={18} />
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)}
                className="filter-select"
              >
                <option value="all">{t('allStatuses') || 'All Statuses'}</option>
                {statusOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <select 
                value={departmentFilter} 
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="filter-select"
              >
                <option value="all">{t('allDepartments') || 'All Departments'}</option>
                {departments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {complaintsLoading ? (
          <div className="complaints-loading">{t('loading') || 'Loading complaints...'}</div>
        ) : complaints.length === 0 ? (
          <div className="no-complaints">{t('noComplaints') || 'No complaints found'}</div>
        ) : (
          <div className="complaints-grid">
            {complaints.map((complaint) => (
              <div key={complaint.id} className="complaint-card">
                <div className="complaint-card-header">
                  <div className="complaint-id-section">
                    <span className="complaint-id-label">ID</span>
                    <span className="complaint-id-value">{complaint.id.substring(0, 8)}</span>
                  </div>
                  <div className="complaint-badges">
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(complaint.status) }}
                    >
                      {getStatusTranslation(complaint.status) || complaint.status}
                    </span>
                    <span 
                      className="urgency-badge"
                      style={{ backgroundColor: getUrgencyColor(complaint.urgency) }}
                    >
                      {getUrgencyTranslation(complaint.urgency) || complaint.urgency}
                    </span>
                  </div>
                </div>
                
                <div className="complaint-card-body">
                  <p className="complaint-description">
                    {complaint.description || 'No description'}
                  </p>
                  
                  <div className="complaint-meta">
                    <div className="meta-item">
                      <span className="meta-label">{t('department') || 'Department'}:</span>
                      <span className="meta-value">
                        {complaint.responsible_department 
                          ? complaint.responsible_department.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">{t('createdAt') || 'Created'}:</span>
                      <span className="meta-value">{formatDate(complaint.created_at)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="complaint-card-footer">
                  {editingStatus === complaint.id ? (
                    <div className="status-edit-form">
                      <select
                        value={complaint.status}
                        onChange={(e) => {
                          const newStatus = e.target.value
                          handleStatusChange(complaint.id, newStatus)
                        }}
                        className="status-select"
                        disabled={updatingStatus === complaint.id}
                      >
                        {statusOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                      <input
                        type="text"
                        placeholder={t('addNotes') || 'Add notes (optional)'}
                        value={statusNotes}
                        onChange={(e) => setStatusNotes(e.target.value)}
                        className="status-notes"
                      />
                      <div className="form-actions">
                        <button
                          onClick={() => {
                            setEditingStatus(null)
                            setStatusNotes('')
                          }}
                          className="btn btn-cancel"
                          disabled={updatingStatus === complaint.id}
                        >
                          {t('cancel') || 'Cancel'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditingStatus(complaint.id)
                        setStatusNotes('')
                      }}
                      className="btn btn-edit-full"
                      disabled={updatingStatus === complaint.id}
                    >
                      <Edit2 size={18} />
                      {t('changeStatus') || 'Change Status'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
