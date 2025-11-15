import axios from 'axios'

// Use relative URL so nginx proxy handles routing to backend
const API_URL = '/api'

// Create axios instance
const api = axios.create({
  baseURL: API_URL
})

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    console.log('🔍 Interceptor Debug:', { 
      url: config.url, 
      method: config.method,
      hasToken: !!token,
      token: token ? `${token.substring(0, 20)}...` : 'NO TOKEN'
    })
    
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
      console.log('✅ Added Authorization header:', config.headers.Authorization.substring(0, 30) + '...')
    } else {
      console.warn('❌ No token found in localStorage')
    }
    
    // Only set default content type for non-FormData requests
    if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    return config
  },
  (error) => {
    console.error('🚨 Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Handle responses and errors
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response Success:', response.config.url, response.status)
    return response
  },
  (error) => {
    console.error('🚨 API Response Error:', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.response?.data?.msg || error.message,
      headers: error.config?.headers
    })
    
    // Handle both 401 Unauthorized and 422 "Subject must be a string" errors
    if (error.response?.status === 401 || 
        (error.response?.status === 422 && error.response?.data?.msg?.includes('Subject must be a string'))) {
      console.warn('🔓 Auth error detected, clearing token and redirecting')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    
    // Also handle "Missing Authorization Header" specifically
    if (error.response?.status === 422 && error.response?.data?.msg?.includes('Missing Authorization Header')) {
      console.error('❌ Missing Authorization Header - Token present in localStorage?', !!localStorage.getItem('token'))
    }
    
    return Promise.reject(error)
  }
)

export default api
