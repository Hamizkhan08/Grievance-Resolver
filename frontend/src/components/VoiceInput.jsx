import React, { useState, useRef, useEffect } from 'react'
import { Mic } from 'lucide-react'
import { useLanguage } from '../contexts/LanguageContext'
import './VoiceInput.css'

/**
 * Reusable Voice Input Component
 * Provides speech-to-text functionality for any input field
 */
const VoiceInput = ({ onTranscript, disabled = false, className = '' }) => {
  const { language } = useLanguage()
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef(null)

  useEffect(() => {
    // Initialize Web Speech API
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        recognitionRef.current = new SpeechRecognition()
        recognitionRef.current.continuous = false
        recognitionRef.current.interimResults = false
        recognitionRef.current.maxAlternatives = 1
        
        // Set language based on selection
        const langMap = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' }
        recognitionRef.current.lang = langMap[language] || 'en-IN'
        
        recognitionRef.current.onresult = (event) => {
          if (event.results.length > 0 && event.results[0].length > 0) {
            const transcript = event.results[0][0].transcript
            if (onTranscript) {
              onTranscript(transcript)
            }
          }
          setIsListening(false)
        }
        
        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
          if (event.error === 'not-allowed') {
            alert('Microphone permission denied. Please enable microphone access in your browser settings.')
          } else if (event.error === 'no-speech') {
            // User didn't speak, just stop listening
            setIsListening(false)
          }
        }
        
        recognitionRef.current.onend = () => {
          setIsListening(false)
        }
      } catch (error) {
        console.error('Failed to initialize speech recognition:', error)
      }
    }
    
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch (e) {
          // Ignore errors on cleanup
        }
      }
    }
  }, [language, onTranscript])

  const startListening = () => {
    if (recognitionRef.current && !isListening && !disabled) {
      try {
        setIsListening(true)
        recognitionRef.current.start()
      } catch (error) {
        console.error('Failed to start speech recognition:', error)
        setIsListening(false)
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
          alert('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.')
        } else {
          alert('Voice input is not available. Please check your browser settings and microphone permissions.')
        }
      }
    } else if (!recognitionRef.current) {
      alert('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.')
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop()
        setIsListening(false)
      } catch (e) {
        setIsListening(false)
      }
    }
  }

  // Check if voice input is supported
  const isSupported = typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)

  if (!isSupported) {
    return null // Don't show button if not supported
  }

  return (
    <button
      type="button"
      className={`voice-input-button ${isListening ? 'listening' : ''} ${className}`}
      onClick={isListening ? stopListening : startListening}
      disabled={disabled}
      aria-label={isListening ? "Stop listening" : "Start voice input"}
      title={isListening ? "Stop listening" : "Voice input"}
    >
      <Mic size={18} />
    </button>
  )
}

export default VoiceInput
