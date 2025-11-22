import React, { createContext, useState, useContext, useEffect } from 'react'

// SSO Authentication Context - EUsuite Single Sign-On
const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    validateSession()
  }, [])

  const validateSession = async () => {
    try {
      console.log('🔐 Validating SSO session...')
      
      // Call /api/auth/validate with cookie credentials
      const response = await fetch('http://192.168.124.50:30500/api/auth/validate', {
        method: 'GET',
        credentials: 'include'
      })
      
      if (response.status === 401) {
        // Not authenticated - redirect to SSO login portal
        console.log('❌ No valid session, redirecting to login portal')
        window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
        return
      }
      
      if (response.status === 200) {
        const data = await response.json()
        if (data.valid && data.user) {
          setUser(data.user)
          console.log('✅ SSO authentication successful:', data.user.email)
        } else {
          console.log('⚠️ Invalid session data, redirecting to login')
          window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
        }
      }
    } catch (error) {
      // Network error or other exception - just log, don't redirect
      console.error('💥 SSO validation error:', error)
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      console.log('🚪 Logging out...')
      
      // Call logout endpoint to delete cookie
      await fetch('http://192.168.124.50:30500/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
      
      // Clear local state
      setUser(null)
      
      // Redirect to login portal
      window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
    } catch (error) {
      console.error('Logout error:', error)
      // Redirect anyway on error
      window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
    }
  }

  const value = {
    user,
    loading,
    logout,
    refreshUser: validateSession
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
