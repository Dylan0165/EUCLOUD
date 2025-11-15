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
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Only set default content type for non-FormData requests
    if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
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
    // Handle both 401 Unauthorized and 422 "Subject must be a string" errors
    if (error.response?.status === 401 || 
        (error.response?.status === 422 && error.response?.data?.msg?.includes('Subject must be a string'))) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
