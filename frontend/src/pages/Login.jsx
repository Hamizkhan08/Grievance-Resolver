import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../hooks/useTranslation'
import { LogIn, Mail, Lock, AlertCircle, UserPlus, Eye, EyeOff } from 'lucide-react'
import './Login.css'

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const { signIn, signUp } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  const from = location.state?.from?.pathname || '/'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (isSignUp) {
      if (password !== confirmPassword) {
        setError('Passwords do not match')
        return
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters')
        return
      }
    }

    setLoading(true)

    try {
      let result
      if (isSignUp) {
        result = await signUp(email, password)
      } else {
        result = await signIn(email, password)
      }
      
      if (result.error) {
        // Show more helpful error messages
        let errorMessage = result.error.message || (isSignUp ? 'Failed to create account' : 'Invalid email or password')
        
        // Add troubleshooting link for configuration errors
        if (errorMessage.includes('Supabase not configured') || errorMessage.includes('Network error')) {
          errorMessage += ' Check LOGIN_TROUBLESHOOTING.md for setup instructions.'
        }
        
        setError(errorMessage)
      } else {
        if (isSignUp && result.data?.user && !result.data.session) {
          // Email confirmation required
          setSuccessMessage('Please check your email to confirm your account before signing in.')
          setError('')
          setIsSignUp(false)
        } else {
          navigate(from, { replace: true })
        }
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* App Branding */}
        <div className="login-brand">
          <div className="brand-logo">🏛️</div>
          <div className="brand-text">
            <h2 className="brand-title">Grievance Resolver</h2>
            <p className="brand-subtitle">AI-Powered Citizen Complaint System</p>
          </div>
        </div>

        {/* Toggle Tabs */}
        <div className="auth-toggle">
          <button 
            type="button"
            className={`auth-toggle-btn ${!isSignUp ? 'active' : ''}`}
            onClick={() => {
              setIsSignUp(false)
              setError('')
              setSuccessMessage('')
              setPassword('')
              setConfirmPassword('')
            }}
          >
            <LogIn size={18} />
            {t('login') || 'Login'}
          </button>
          <button 
            type="button"
            className={`auth-toggle-btn ${isSignUp ? 'active' : ''}`}
            onClick={() => {
              setIsSignUp(true)
              setError('')
              setSuccessMessage('')
              setPassword('')
              setConfirmPassword('')
            }}
          >
            <UserPlus size={18} />
            {t('signUp') || 'Sign Up'}
          </button>
        </div>

        <div className="login-header">
          <h1>{isSignUp ? (t('signUpTitle') || 'Create Account') : (t('loginTitle') || 'Login')}</h1>
          <p>{isSignUp ? (t('signUpSubtitle') || 'Create a new account to file complaints') : (t('loginSubtitle') || 'Sign in to access your account')}</p>
        </div>

        {successMessage && (
          <div className="login-success">
            <AlertCircle size={18} />
            <span>{successMessage}</span>
          </div>
        )}

        {error && (
          <div className="login-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">
              <Mail size={18} />
              {t('email') || 'Email'}
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('emailPlaceholder') || 'Enter your email'}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={18} />
              {t('password') || 'Password'}
            </label>
            <div className="password-input-wrapper">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('passwordPlaceholder') || 'Enter your password'}
                required
                autoComplete={isSignUp ? 'new-password' : 'current-password'}
                minLength={6}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {isSignUp && (
            <div className="form-group">
              <label htmlFor="confirmPassword">
                <Lock size={18} />
                {t('confirmPassword') || 'Confirm Password'}
              </label>
              <div className="password-input-wrapper">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t('confirmPasswordPlaceholder') || 'Confirm your password'}
                  required
                  autoComplete="new-password"
                  minLength={6}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          )}

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading 
              ? (isSignUp ? (t('creatingAccount') || 'Creating account...') : (t('loggingIn') || 'Logging in...'))
              : (isSignUp ? (t('signUp') || 'Sign Up') : (t('login') || 'Login'))
            }
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
