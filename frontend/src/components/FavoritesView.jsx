import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Star, Download, Trash2, ExternalLink } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import './FavoritesView.css'

function FavoritesView({ onClose, onFileClick }) {
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFavorites()
  }, [])

  const loadFavorites = async () => {
    try {
      setLoading(true)
      const response = await axios.get('http://localhost:5000/api/favorites/list')
      setFavorites(response.data.files)
    } catch (error) {
      console.error('Failed to load favorites:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeFavorite = async (fileId) => {
    try {
      await axios.post(`http://localhost:5000/api/favorites/toggle/${fileId}`)
      setFavorites(favorites.filter(file => file.id !== fileId))
    } catch (error) {
      console.error('Failed to remove favorite:', error)
    }
  }

  const downloadFile = async (file) => {
    try {
      const response = await axios.get(
        `http://localhost:5000/api/files/download/${file.id}`,
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="favorites-modal-overlay" onClick={onClose}>
      <div className="favorites-modal" onClick={(e) => e.stopPropagation()}>
        <div className="favorites-header">
          <h2>
            <Star size={24} style={{ color: '#ffc107' }} />
            Favorites
          </h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="favorites-content">
          {loading ? (
            <div className="favorites-loading">Loading favorites...</div>
          ) : favorites.length === 0 ? (
            <div className="favorites-empty">
              <Star size={48} style={{ color: '#ddd' }} />
              <p>No favorites yet</p>
              <p className="favorites-empty-hint">
                Click the star icon on any file to add it to favorites
              </p>
            </div>
          ) : (
            <div className="favorites-list">
              {favorites.map((file) => (
                <div key={file.id} className="favorite-item">
                  <div className="favorite-info" onClick={() => onFileClick(file)}>
                    <div className="favorite-name">
                      <Star size={16} style={{ color: '#ffc107', marginRight: '8px' }} />
                      {file.filename}
                    </div>
                    <div className="favorite-meta">
                      <span>{formatFileSize(file.size)}</span>
                      <span>•</span>
                      <span>Modified {formatDistanceToNow(new Date(file.updated_at))} ago</span>
                    </div>
                  </div>
                  <div className="favorite-actions">
                    <button
                      onClick={() => downloadFile(file)}
                      title="Download"
                    >
                      <Download size={18} />
                    </button>
                    <button
                      onClick={() => onFileClick(file)}
                      title="Open"
                    >
                      <ExternalLink size={18} />
                    </button>
                    <button
                      onClick={() => removeFavorite(file.id)}
                      title="Remove from favorites"
                      className="remove-favorite-btn"
                    >
                      <Star size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FavoritesView
