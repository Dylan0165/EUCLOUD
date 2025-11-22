import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import { AuthProvider, useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import './App.css'

function AppContent() {
  const { user, loading } = useAuth()
  
  // Show loading screen while validating SSO session
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Verifying SSO authentication...</p>
      </div>
    )
  }
  
  // If no user after loading, AuthContext has already redirected to login portal
  // Only render app if user is authenticated
  if (!user) {
    return (
      <div className="loading-screen">
        <p>Redirecting to login portal...</p>
      </div>
    )
  }
  
  // User is authenticated, render the app
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/eucloud" element={<Dashboard />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
        <ToastContainer 
          position="bottom-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="colored"
        />
      </div>
    </Router>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
