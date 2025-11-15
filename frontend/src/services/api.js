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
    
    if (token) {
      // Set Authorization header with Bearer token
      config.headers = config.headers || {}
      config.headers['Authorization'] = `Bearer ${token}`
    }
    
    // Set default content type for non-FormData requests
    // For FormData, browser will set multipart/form-data with boundary automatically
    if (config.data && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = config.headers['Content-Type'] || 'application/json'
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle responses and errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized or JWT errors
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    
    // Handle 422 validation errors that might be JWT-related
    if (error.response?.status === 422) {
      const errorMsg = error.response?.data?.msg || ''
      if (errorMsg.includes('Subject must be a string') || 
          errorMsg.includes('Missing Authorization Header')) {
        console.error('JWT/Auth error:', errorMsg)
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
