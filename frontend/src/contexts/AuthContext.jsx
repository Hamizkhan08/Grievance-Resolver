import React, { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [userRole, setUserRole] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check if user is admin based on email
  const isAdmin = (email) => {
    return email === 'resolvergrievance@gmail.com'
  }

  useEffect(() => {
    // Check if Supabase is properly configured
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
    
    if (!supabaseUrl || !supabaseAnonKey) {
      // If Supabase is not configured, skip auth initialization
      console.warn('⚠️ Supabase not configured. Authentication disabled.')
      setLoading(false)
      return
    }

    // Get initial session
    supabase.auth.getSession()
      .then(({ data: { session }, error }) => {
        if (error) {
          console.error('Error getting session:', error)
          setLoading(false)
          return
        }
        if (session?.user) {
          setUser(session.user)
          const role = isAdmin(session.user.email) ? 'admin' : 'citizen'
          setUserRole(role)
        }
        setLoading(false)
      })
      .catch((error) => {
        console.error('Error in getSession:', error)
        setLoading(false)
      })

    // Listen for auth changes
    let subscription
    try {
      const {
        data: { subscription: sub },
      } = supabase.auth.onAuthStateChange((_event, session) => {
        if (session?.user) {
          setUser(session.user)
          const role = isAdmin(session.user.email) ? 'admin' : 'citizen'
          setUserRole(role)
        } else {
          setUser(null)
          setUserRole(null)
        }
        setLoading(false)
      })
      subscription = sub
    } catch (error) {
      console.error('Error setting up auth state listener:', error)
      setLoading(false)
    }

    return () => {
      if (subscription) {
        subscription.unsubscribe()
      }
    }
  }, [])

  const signIn = async (email, password) => {
    try {
      // Check if Supabase is configured
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
      
      if (!supabaseUrl || !supabaseAnonKey || supabaseUrl === '' || supabaseAnonKey === '') {
        return { 
          data: null, 
          error: { 
            message: 'Supabase not configured. Please check your .env file. See LOGIN_TROUBLESHOOTING.md for help.' 
          } 
        }
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        // Provide more helpful error messages
        let errorMessage = error.message
        
        if (error.message.includes('Invalid login credentials')) {
          errorMessage = 'Invalid email or password. Please check your credentials.'
        } else if (error.message.includes('Email not confirmed')) {
          errorMessage = 'Please check your email and confirm your account before signing in.'
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          errorMessage = 'Failed to connect to Supabase. Please check your internet connection and Supabase configuration. See LOGIN_TROUBLESHOOTING.md for help.'
        }
        
        return { data: null, error: { ...error, message: errorMessage } }
      }

      if (data?.user) {
        const role = isAdmin(data.user.email) ? 'admin' : 'citizen'
        setUserRole(role)
      }

      return { data, error: null }
    } catch (error) {
      console.error('Sign in error:', error)
      
      // Handle network errors
      if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
        return { 
          data: null, 
          error: { 
            message: 'Network error: Cannot connect to Supabase. Please check your .env file and ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set correctly. See LOGIN_TROUBLESHOOTING.md for help.' 
          } 
        }
      }
      
      return { data: null, error }
    }
  }

  const signUp = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })

      if (error) throw error

      if (data?.user) {
        const role = isAdmin(data.user.email) ? 'admin' : 'citizen'
        setUserRole(role)
      }

      return { data, error: null }
    } catch (error) {
      console.error('Sign up error:', error)
      return { data: null, error }
    }
  }

  const signInWithGoogle = async () => {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/`,
        },
      })

      if (error) throw error

      return { data, error: null }
    } catch (error) {
      console.error('Google sign in error:', error)
      return { data: null, error }
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      setUser(null)
      setUserRole(null)
      return { error: null }
    } catch (error) {
      console.error('Sign out error:', error)
      return { error }
    }
  }

  const value = {
    user,
    userRole,
    loading,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    isAdmin: userRole === 'admin',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
