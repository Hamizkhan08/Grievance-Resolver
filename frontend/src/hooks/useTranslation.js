import { useLanguage } from '../contexts/LanguageContext'
import { translations } from '../translations'

export const useTranslation = () => {
  const { language } = useLanguage()
  
  const t = (key) => {
    return translations[language]?.[key] || translations.en[key] || key
  }
  
  // Helper to get status translation
  const getStatusTranslation = (status) => {
    const statusMap = {
      'open': 'statusOpen',
      'in_progress': 'statusInProgress',
      'escalated': 'statusEscalated',
      'resolved': 'statusResolved',
      'closed': 'statusClosed'
    }
    const key = statusMap[status] || `status${status.charAt(0).toUpperCase() + status.slice(1)}`
    return t(key)
  }
  
  // Helper to get urgency translation
  const getUrgencyTranslation = (urgency) => {
    const urgencyMap = {
      'low': 'urgencyLow',
      'medium': 'urgencyMedium',
      'high': 'urgencyHigh',
      'urgent': 'urgencyUrgent'
    }
    const key = urgencyMap[urgency] || `urgency${urgency.charAt(0).toUpperCase() + urgency.slice(1)}`
    return t(key)
  }
  
  return { t, getStatusTranslation, getUrgencyTranslation }
}
