import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { MapPin, TrendingUp, Clock, BarChart3, Filter } from 'lucide-react'
import { useTranslation } from '../hooks/useTranslation'
import './Heatmap.css'
import { API_URL as API_BASE_URL } from '../lib/config'

const Heatmap = () => {
  const { t } = useTranslation()
  const [heatmapData, setHeatmapData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    state: '',
    city: '',
    days: 30
  })

  useEffect(() => {
    fetchHeatmapData()
  }, [filters])

  const fetchHeatmapData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (filters.state) params.state = filters.state
      if (filters.city) params.city = filters.city
      params.days = filters.days

      const response = await axios.get(`${API_BASE_URL}/api/heatmap/data`, { params })
      if (response.data.success) {
        setHeatmapData(response.data.data)
      } else {
        setError(response.data.error || 'Failed to load heatmap data')
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to fetch heatmap data')
      console.error('Heatmap error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getDensityColor = (count) => {
    if (count >= 50) return '#dc2626' // Red - high density
    if (count >= 20) return '#f59e0b' // Orange - medium-high
    if (count >= 10) return '#eab308' // Yellow - medium
    if (count >= 5) return '#84cc16' // Light green - low-medium
    return '#10b981' // Green - low density
  }

  const getSentimentColor = (score) => {
    if (score <= -0.5) return '#dc2626' // Red - very negative
    if (score <= -0.2) return '#f59e0b' // Orange - negative
    if (score <= 0.2) return '#eab308' // Yellow - neutral
    return '#10b981' // Green - positive
  }

  if (loading) {
    return (
      <div className="heatmap-loading">
        <div className="loading-spinner"></div>
        <p>{t('heatmapLoading') || 'Loading heatmap data...'}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="heatmap-error">
        <p>{error}</p>
        <button onClick={fetchHeatmapData} className="btn btn-primary">
          {t('retry') || 'Retry'}
        </button>
      </div>
    )
  }

  return (
    <div className="heatmap">
      <div className="heatmap-header">
        <div>
          <h1>{t('heatmapTitle') || 'Real-Time Grievance Heatmap'}</h1>
          <p>{t('heatmapSubtitle') || 'Complaint density, categories, and resolution times by location'}</p>
        </div>
        <div className="heatmap-filters">
          <Filter size={18} />
          <select
            value={filters.state}
            onChange={(e) => setFilters({ ...filters, state: e.target.value })}
            className="filter-select"
          >
            <option value="">{t('allStates') || 'All States'}</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Delhi">Delhi</option>
          </select>
          <select
            value={filters.days}
            onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
            className="filter-select"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      {heatmapData && (
        <>
          {/* Summary Cards */}
          <div className="heatmap-summary">
            <div className="summary-card">
              <MapPin size={24} />
              <div>
                <span className="summary-label">{t('totalLocations') || 'Total Locations'}</span>
                <span className="summary-value">{heatmapData.summary?.total_locations || 0}</span>
              </div>
            </div>
            <div className="summary-card">
              <BarChart3 size={24} />
              <div>
                <span className="summary-label">{t('totalComplaints') || 'Total Complaints'}</span>
                <span className="summary-value">{heatmapData.summary?.total_complaints || 0}</span>
              </div>
            </div>
            <div className="summary-card">
              <TrendingUp size={24} />
              <div>
                <span className="summary-label">{t('categories') || 'Categories'}</span>
                <span className="summary-value">{heatmapData.summary?.total_categories || 0}</span>
              </div>
            </div>
            <div className="summary-card">
              <Clock size={24} />
              <div>
                <span className="summary-label">{t('departments') || 'Departments'}</span>
                <span className="summary-value">{heatmapData.summary?.total_departments || 0}</span>
              </div>
            </div>
          </div>

          {/* Location Heatmap */}
          <div className="heatmap-section">
            <h2>{t('complaintDensity') || 'Complaint Density by Location'}</h2>
            <div className="locations-grid">
              {heatmapData.locations?.map((location, idx) => (
                <div key={idx} className="location-card">
                  <div className="location-header">
                    <MapPin size={16} />
                    <div>
                      <h3>{location.location.city || 'Unknown'}</h3>
                      <p className="location-details">
                        {location.location.district && `${location.location.district}, `}
                        {location.location.state}
                      </p>
                    </div>
                    <div
                      className="density-indicator"
                      style={{ backgroundColor: getDensityColor(location.complaint_count) }}
                    >
                      {location.complaint_count}
                    </div>
                  </div>

                  <div className="location-stats">
                    <div className="stat-item">
                      <span className="stat-label">{t('complaints') || 'Complaints'}</span>
                      <span className="stat-value">{location.complaint_count}</span>
                    </div>
                    {location.avg_resolution_hours && (
                      <div className="stat-item">
                        <span className="stat-label">{t('avgResolution') || 'Avg Resolution'}</span>
                        <span className="stat-value">
                          {Math.round(location.avg_resolution_hours / 24)} {t('days') || 'days'}
                        </span>
                      </div>
                    )}
                    {location.sentiment_avg !== 0 && (
                      <div className="stat-item">
                        <span className="stat-label">{t('sentiment') || 'Sentiment'}</span>
                        <span
                          className="stat-value"
                          style={{ color: getSentimentColor(location.sentiment_avg) }}
                        >
                          {location.sentiment_avg > 0 ? '+' : ''}{location.sentiment_avg.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Top Categories */}
                  {Object.keys(location.categories).length > 0 && (
                    <div className="location-categories">
                      <span className="categories-label">{t('topCategories') || 'Top Categories'}</span>
                      <div className="categories-list">
                        {Object.entries(location.categories)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 3)
                          .map(([cat, count]) => (
                            <span key={cat} className="category-tag">
                              {cat}: {count}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Departments */}
                  {Object.keys(location.departments).length > 0 && (
                    <div className="location-departments">
                      <span className="departments-label">{t('departments') || 'Departments'}</span>
                      <div className="departments-list">
                        {Object.entries(location.departments)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 2)
                          .map(([dept, count]) => (
                            <span key={dept} className="department-tag">
                              {dept}: {count}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Top Categories */}
          {heatmapData.top_categories && heatmapData.top_categories.length > 0 && (
            <div className="heatmap-section">
              <h2>{t('topIssueCategories') || 'Top Issue Categories'}</h2>
              <div className="categories-chart">
                {heatmapData.top_categories.map((item, idx) => (
                  <div key={idx} className="category-bar">
                    <div className="category-label">{item.category}</div>
                    <div className="bar-container">
                      <div
                        className="bar"
                        style={{
                          width: `${(item.count / heatmapData.top_categories[0].count) * 100}%`
                        }}
                      >
                        {item.count}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Department Stats */}
          {heatmapData.department_stats && Object.keys(heatmapData.department_stats).length > 0 && (
            <div className="heatmap-section">
              <h2>{t('resolutionTimesByDepartment') || 'Average Resolution Times by Department'}</h2>
              <div className="department-stats-grid">
                {Object.entries(heatmapData.department_stats).map(([dept, stats]) => (
                  <div key={dept} className="department-stat-card">
                    <h3>{dept}</h3>
                    <div className="stat-row">
                      <span>{t('avgResolution') || 'Avg Resolution'}</span>
                      <span className="stat-value">
                        {Math.round(stats.avg_resolution_hours / 24)} {t('days') || 'days'}
                      </span>
                    </div>
                    <div className="stat-row">
                      <span>{t('totalComplaints') || 'Total Complaints'}</span>
                      <span className="stat-value">{stats.total_complaints}</span>
                    </div>
                    <div className="stat-row">
                      <span>{t('resolutionRate') || 'Resolution Rate'}</span>
                      <span className="stat-value">
                        {(stats.resolution_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Heatmap
