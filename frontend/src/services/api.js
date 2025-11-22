import axios from 'axios'

// Use relative URL so nginx proxy handles routing to backend
const API_URL = '/api'

// Create axios instance with SSO cookie credentials
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,  // Include cookies in all requests for SSO
  credentials: 'include'
})

// Add default headers
api.interceptors.request.use(
  (config) => {
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
    // Handle 401 Unauthorized - redirect to SSO login portal
    if (error.response?.status === 401) {
      console.log('🔒 401 Unauthorized - redirecting to SSO login portal')
      window.location.href = 'http://192.168.124.50:30090/login?redirect=/eucloud'
    }
    
    return Promise.reject(error)
  }
)

export default api
