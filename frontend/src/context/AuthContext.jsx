import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'
import { SSO_CONFIG, buildLoginRedirectUrl } from '../config/sso'

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
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      // Check SSO session via /auth/me with cookie credentials
      const response = await axios.get(SSO_CONFIG.AUTH_CHECK_URL, {
        withCredentials: true,
        credentials: 'include'
      })
      
      if (response.status === 200 && response.data.user) {
        setUser(response.data.user)
      } else {
        // No valid session, redirect to SSO login portal
        redirectToSSOLogin()
      }
    } catch (error) {
      if (error.response?.status === 401) {
        // Unauthorized - redirect to SSO login portal
        redirectToSSOLogin()
      } else {
        console.error('SSO auth check failed:', error)
        // On other errors, also redirect to login for safety
        redirectToSSOLogin()
      }
    } finally {
      setLoading(false)
    }
  }

  const redirectToSSOLogin = () => {
    window.location.href = buildLoginRedirectUrl()
  }

  const logout = () => {
    // Logout is handled by EUsuite Login Portal
    // Just clear local state and redirect
    setUser(null)
    redirectToSSOLogin()
  }

  const value = {
    user,
    loading,
    logout,
    refreshUser: checkAuth
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
