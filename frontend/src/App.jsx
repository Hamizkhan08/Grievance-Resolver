import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LanguageProvider } from './contexts/LanguageContext'
import { AuthProvider } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import ComplaintStatus from './pages/ComplaintStatus'
import Dashboard from './pages/Dashboard'
import Heatmap from './pages/Heatmap'
import Forums from './pages/Forums'
import Forum from './pages/Forum'
import Chatbot from './components/Chatbot'
import './App.css'

function App() {
  console.log('📱 App component rendering...')
  
  // Check if Supabase is configured
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
  const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
  
  if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('⚠️ Supabase not configured. Some features may not work.')
  }
  
  return (
    <ErrorBoundary>
      <AuthProvider>
        <LanguageProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="*" element={
                <Layout>
                  <Routes>
                    <Route 
                      path="/" 
                      element={
                        <ProtectedRoute>
                          <Home />
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="/status/:id?" 
                      element={
                        <ProtectedRoute>
                          <ComplaintStatus />
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="/dashboard" 
                      element={
                        <ProtectedRoute requireAdmin={true}>
                          <Dashboard />
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="/heatmap" 
                      element={
                        <ProtectedRoute>
                          <Heatmap />
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="/forums" 
                      element={
                        <ProtectedRoute>
                          <Forums />
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="/forum/:complaintId" 
                      element={
                        <ProtectedRoute>
                          <Forum />
                        </ProtectedRoute>
                      } 
                    />
                  </Routes>
                  <Chatbot />
                </Layout>
              } />
            </Routes>
          </Router>
        </LanguageProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

