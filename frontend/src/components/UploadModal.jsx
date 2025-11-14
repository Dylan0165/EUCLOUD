import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { fileService } from '../services'
import { toast } from 'react-toastify'
import { Upload, X, File, CheckCircle, AlertCircle } from 'lucide-react'
import './UploadModal.css'

function UploadModal({ currentFolder, onClose, onComplete }) {
  const [uploads, setUploads] = useState([])

  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach(file => {
      const uploadId = Date.now() + Math.random()
      
      setUploads(prev => [...prev, {
        id: uploadId,
        file,
        progress: 0,
        status: 'uploading', // 'uploading', 'success', 'error'
        error: null
      }])

      fileService.upload(
        file,
        currentFolder,
        (progress) => {
          setUploads(prev => prev.map(u =>
            u.id === uploadId ? { ...u, progress } : u
          ))
        }
      )
      .then(() => {
        setUploads(prev => prev.map(u =>
          u.id === uploadId ? { ...u, status: 'success', progress: 100 } : u
        ))
        toast.success(`${file.name} uploaded successfully`)
      })
      .catch((error) => {
        setUploads(prev => prev.map(u =>
          u.id === uploadId ? { 
            ...u, 
            status: 'error', 
            error: error.response?.data?.error || 'Upload failed' 
          } : u
        ))
        toast.error(`Failed to upload ${file.name}`)
      })
    })
  }, [currentFolder])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    multiple: true
  })

  const handleClose = () => {
    const hasUploading = uploads.some(u => u.status === 'uploading')
    if (hasUploading) {
      if (!window.confirm('Files are still uploading. Are you sure you want to close?')) {
        return
      }
    }
    
    const hasSuccess = uploads.some(u => u.status === 'success')
    if (hasSuccess) {
      onComplete()
    } else {
      onClose()
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
    <div className="modal-backdrop" onClick={handleClose}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Upload Files</h2>
          <button className="btn-icon" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <Upload size={48} className="dropzone-icon" />
            {isDragActive ? (
              <p>Drop files here...</p>
            ) : (
              <>
                <p>Drag & drop files here, or click to select files</p>
                <p className="dropzone-hint">Maximum file size: 100MB</p>
              </>
            )}
          </div>

          {uploads.length > 0 && (
            <div className="uploads-list">
              <h3>Uploading {uploads.length} file(s)</h3>
              {uploads.map(upload => (
                <div key={upload.id} className="upload-item">
                  <div className="upload-item-icon">
                    {upload.status === 'success' ? (
                      <CheckCircle size={20} className="success-icon" />
                    ) : upload.status === 'error' ? (
                      <AlertCircle size={20} className="error-icon" />
                    ) : (
                      <File size={20} />
                    )}
                  </div>
                  <div className="upload-item-info">
                    <p className="upload-item-name">{upload.file.name}</p>
                    <p className="upload-item-size">{formatBytes(upload.file.size)}</p>
                    {upload.error && (
                      <p className="upload-item-error">{upload.error}</p>
                    )}
                  </div>
                  <div className="upload-item-progress">
                    {upload.status === 'uploading' && (
                      <>
                        <div className="progress-bar">
                          <div 
                            className="progress-bar-fill"
                            style={{ width: `${upload.progress}%` }}
                          />
                        </div>
                        <span className="progress-text">{upload.progress}%</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={handleClose}>
            {uploads.some(u => u.status === 'success') ? 'Done' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default UploadModal
