import React, { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { Trash2, RotateCcw, X, AlertTriangle } from 'lucide-react'
import api from '../services/api'
import { format } from 'date-fns'
import './TrashModal.css'

function TrashModal({ onClose, onRestore }) {
  const [trashedFiles, setTrashedFiles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTrash()
  }, [])

  const loadTrash = async () => {
    try {
      const response = await api.get('/trash/list')
      setTrashedFiles(response.data.files)
    } catch (error) {
      toast.error('Failed to load trash')
    } finally {
      setLoading(false)
    }
  }

  const handleRestore = async (fileId) => {
    try {
      await api.post(`/trash/restore/${fileId}`)
      toast.success('File restored successfully')
      loadTrash()
      if (onRestore) onRestore()
    } catch (error) {
      toast.error('Failed to restore file')
    }
  }

  const handlePermanentDelete = async (fileId) => {
    if (!window.confirm('Permanently delete this file? This cannot be undone.')) {
      return
    }

    try {
      await api.delete(`/trash/permanent-delete/${fileId}`)
      toast.success('File permanently deleted')
      loadTrash()
    } catch (error) {
      toast.error('Failed to delete file')
    }
  }

  const handleEmptyTrash = async () => {
    if (!window.confirm('Empty entire trash? All files will be permanently deleted. This cannot be undone.')) {
      return
    }

    try {
      await api.post('/trash/empty')
      toast.success('Trash emptied')
      loadTrash()
      if (onRestore) onRestore()
    } catch (error) {
      toast.error('Failed to empty trash')
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="trash-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-section">
            <Trash2 size={24} />
            <h2>Trash</h2>
          </div>
          <div className="modal-actions-header">
            {trashedFiles.length > 0 && (
              <button className="btn btn-danger" onClick={handleEmptyTrash}>
                <AlertTriangle size={18} />
                Empty Trash
              </button>
            )}
            <button className="btn-icon" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="trash-loading">Loading...</div>
          ) : trashedFiles.length === 0 ? (
            <div className="trash-empty">
              <Trash2 size={64} className="trash-empty-icon" />
              <h3>Trash is empty</h3>
              <p>Deleted files will appear here</p>
            </div>
          ) : (
            <div className="trash-list">
              {trashedFiles.map(file => (
                <div key={file.file_id} className="trash-item">
                  <div className="trash-item-info">
                    <p className="trash-item-name">{file.filename}</p>
                    <p className="trash-item-meta">
                      {formatBytes(file.file_size)} • 
                      Deleted {file.deleted_at ? format(new Date(file.deleted_at), 'MMM dd, yyyy') : 'Unknown'}
                    </p>
                  </div>
                  <div className="trash-item-actions">
                    <button 
                      className="btn btn-secondary"
                      onClick={() => handleRestore(file.file_id)}
                      title="Restore"
                    >
                      <RotateCcw size={18} />
                      Restore
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handlePermanentDelete(file.file_id)}
                      title="Delete permanently"
                    >
                      <Trash2 size={18} />
                      Delete
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

export default TrashModal
