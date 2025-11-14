import React from 'react'
import { X, Download } from 'lucide-react'
import { fileService } from '../services'
import './FilePreviewModal.css'

function FilePreviewModal({ file, onClose, onDownload }) {
  const getPreviewContent = () => {
    const mimeType = file.mime_type

    // Images
    if (mimeType?.startsWith('image/')) {
      return (
        <img
          src={fileService.getPreviewUrl(file.file_id)}
          alt={file.filename}
          className="preview-image"
        />
      )
    }

    // PDFs
    if (mimeType === 'application/pdf') {
      return (
        <iframe
          src={fileService.getPreviewUrl(file.file_id)}
          className="preview-iframe"
          title={file.filename}
        />
      )
    }

    // Text files
    if (mimeType?.includes('text') || 
        ['application/json', 'application/javascript'].includes(mimeType)) {
      return (
        <iframe
          src={fileService.getPreviewUrl(file.file_id)}
          className="preview-iframe"
          title={file.filename}
        />
      )
    }

    // Video
    if (mimeType?.startsWith('video/')) {
      return (
        <video
          src={fileService.getPreviewUrl(file.file_id)}
          controls
          className="preview-video"
        >
          Your browser does not support video playback.
        </video>
      )
    }

    // Audio
    if (mimeType?.startsWith('audio/')) {
      return (
        <div className="preview-audio-container">
          <audio
            src={fileService.getPreviewUrl(file.file_id)}
            controls
            className="preview-audio"
          >
            Your browser does not support audio playback.
          </audio>
        </div>
      )
    }

    // Fallback
    return (
      <div className="preview-fallback">
        <p>Preview not available for this file type</p>
        <button className="btn btn-primary" onClick={onDownload}>
          <Download size={18} />
          Download to view
        </button>
      </div>
    )
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="preview-header">
          <div className="preview-title">
            <h2>{file.filename}</h2>
            <p className="preview-meta">
              {file.mime_type} • {formatBytes(file.file_size)}
            </p>
          </div>
          <div className="preview-actions">
            <button className="btn btn-secondary" onClick={onDownload}>
              <Download size={18} />
              Download
            </button>
            <button className="btn-icon" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>
        
        <div className="preview-content">
          {getPreviewContent()}
        </div>
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

export default FilePreviewModal
