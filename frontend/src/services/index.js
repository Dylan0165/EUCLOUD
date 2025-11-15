import api from './api'

export const authService = {
  // Register new user
  register: async (email, password) => {
    const response = await api.post('/auth/register', { email, password })
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
    }
    return response.data
  },

  // Login
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password })
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
    }
    return response.data
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      // Always remove token and redirect, even if API call fails
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data.user
  }
}

export const fileService = {
  // Upload file
  upload: async (file, folderId, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    if (folderId) {
      formData.append('folder_id', folderId)
    }

    const response = await api.post('/files/upload', formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })
    return response.data
  },

  // List files
  list: async (folderId = null) => {
    const response = await api.get('/files/list', {
      params: { folder_id: folderId }
    })
    return response.data
  },

  // Get file details
  get: async (fileId) => {
    const response = await api.get(`/files/${fileId}`)
    return response.data.file
  },

  // Download file
  download: async (fileId, filename) => {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },

  // Rename file
  rename: async (fileId, filename) => {
    const response = await api.put(`/files/${fileId}/rename`, { filename })
    return response.data
  },

  // Delete file
  delete: async (fileId) => {
    const response = await api.delete(`/files/${fileId}`)
    return response.data
  },

  // Move file
  move: async (fileId, folderId) => {
    const response = await api.post(`/files/${fileId}/move`, { folder_id: folderId })
    return response.data
  },

  // Copy file
  copy: async (fileId, folderId) => {
    const response = await api.post(`/files/${fileId}/copy`, { folder_id: folderId })
    return response.data
  },

  // Get preview URL
  getPreviewUrl: (fileId) => {
    const token = localStorage.getItem('token')
    return `/api/files/${fileId}/preview?token=${token}`
  }
}

export const folderService = {
  // Create folder
  create: async (folderName, parentFolderId = null) => {
    const response = await api.post('/folders/create', {
      folder_name: folderName,
      parent_folder_id: parentFolderId
    })
    return response.data
  },

  // List all folders
  list: async () => {
    const response = await api.get('/folders/list')
    return response.data.folders
  },

  // Get folder
  get: async (folderId) => {
    const response = await api.get(`/folders/${folderId}`)
    return response.data.folder
  },

  // Rename folder
  rename: async (folderId, folderName) => {
    const response = await api.put(`/folders/${folderId}/rename`, { folder_name: folderName })
    return response.data
  },

  // Delete folder
  delete: async (folderId) => {
    const response = await api.delete(`/folders/${folderId}`)
    return response.data
  }
}

export const shareService = {
  // Create share
  create: async (fileId, options = {}) => {
    const response = await api.post('/share/create', {
      file_id: fileId,
      access_type: options.accessType || 'view',
      expires_in_days: options.expiresInDays,
      password: options.password
    })
    return response.data
  },

  // Get share
  get: async (shareId, password = null) => {
    const response = await api.get(`/share/${shareId}`, {
      params: { password }
    })
    return response.data
  },

  // Delete share
  delete: async (shareId) => {
    const response = await api.delete(`/share/${shareId}`)
    return response.data
  }
}

export const storageService = {
  // Get storage usage
  getUsage: async () => {
    const response = await api.get('/storage/usage')
    return response.data
  },

  // Get storage stats
  getStats: async () => {
    const response = await api.get('/storage/stats')
    return response.data
  }
}
