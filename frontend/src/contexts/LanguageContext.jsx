import React, { createContext, useContext, useState, useEffect } from 'react'

const LanguageContext = createContext()

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider')
  }
  return context
}

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    // Load from localStorage or default to English
    // Check if we're in browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      return localStorage.getItem('app_language') || 'en'
    }
    return 'en'
  })

  useEffect(() => {
    // Save to localStorage whenever language changes
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem('app_language', language)
    }
  }, [language])

  const changeLanguage = (lang) => {
    setLanguage(lang)
  }

  return (
    <LanguageContext.Provider value={{ language, changeLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}
