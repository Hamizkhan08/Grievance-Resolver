import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../hooks/useTranslation'
import { LogIn, Mail, Lock, AlertCircle, UserPlus } from 'lucide-react'
import './Login.css'

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const { signIn, signUp, signInWithGoogle } = useAuth()
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
          setError('Please check your email to confirm your account before signing in.')
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

  const handleGoogleSignIn = async () => {
    setError('')
    setGoogleLoading(true)

    try {
      const { error } = await signInWithGoogle()
      if (error) {
        setError(error.message || 'Failed to sign in with Google')
      }
      // OAuth redirect will handle navigation
    } catch (err) {
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setGoogleLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">
            {isSignUp ? <UserPlus size={32} /> : <LogIn size={32} />}
          </div>
          <h1>{isSignUp ? (t('signUpTitle') || 'Create Account') : (t('loginTitle') || 'Login')}</h1>
          <p>{isSignUp ? (t('signUpSubtitle') || 'Create a new account to file complaints') : (t('loginSubtitle') || 'Sign in to access your account')}</p>
        </div>

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
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('passwordPlaceholder') || 'Enter your password'}
              required
              autoComplete={isSignUp ? 'new-password' : 'current-password'}
              minLength={6}
            />
          </div>

          {isSignUp && (
            <div className="form-group">
              <label htmlFor="confirmPassword">
                <Lock size={18} />
                {t('confirmPassword') || 'Confirm Password'}
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t('confirmPasswordPlaceholder') || 'Confirm your password'}
                required
                autoComplete="new-password"
                minLength={6}
              />
            </div>
          )}

          <button 
            type="submit" 
            className="login-button"
            disabled={loading || googleLoading}
          >
            {loading 
              ? (isSignUp ? (t('creatingAccount') || 'Creating account...') : (t('loggingIn') || 'Logging in...'))
              : (isSignUp ? (t('signUp') || 'Sign Up') : (t('login') || 'Login'))
            }
          </button>
        </form>

        <div className="login-divider">
          <span>{t('or') || 'or'}</span>
        </div>

        <button 
          onClick={handleGoogleSignIn}
          className="google-button"
          disabled={googleLoading || loading}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.965-2.184l-2.908-2.258c-.806.54-1.837.86-3.057.86-2.35 0-4.34-1.587-5.053-3.72H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/>
            <path d="M3.947 10.698c-.18-.54-.282-1.117-.282-1.698s.102-1.158.282-1.698V4.97H.957C.348 6.175 0 7.55 0 9s.348 2.825.957 4.03l2.99-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.97L3.947 7.302C4.66 5.167 6.65 3.58 9 3.58z" fill="#EA4335"/>
          </svg>
          {googleLoading ? (t('signingInWithGoogle') || 'Signing in...') : (t('signInWithGoogle') || 'Sign in with Google')}
        </button>

        <div className="login-footer">
          <p>
            {isSignUp 
              ? (t('alreadyHaveAccount') || 'Already have an account? ')
              : (t('dontHaveAccount') || "Don't have an account? ")
            }
            <button 
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp)
                setError('')
                setPassword('')
                setConfirmPassword('')
              }}
              className="link-button"
            >
              {isSignUp ? (t('login') || 'Login') : (t('signUp') || 'Sign Up')}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
