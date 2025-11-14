import React, { useState } from 'react'
import { 
  Folder, File as FileIcon, Image, FileText, Film, Music,
  Download, Trash2, Edit, Share2, MoreVertical, Eye, Star
} from 'lucide-react'
import { format } from 'date-fns'
import api from '../services/api'
import { toast } from 'react-toastify'
import './FileBrowser.css'

function FileBrowser({
  files,
  folders,
  viewMode,
  loading,
  currentFolder,
  onFolderClick,
  onFileClick,
  onFileDownload,
  onFileDelete,
  onFileRename,
  onFileShare,
  onFolderDelete
}) {
  const [contextMenu, setContextMenu] = useState(null)
  const [selectedItems, setSelectedItems] = useState([])
  const [renamingItem, setRenamingItem] = useState(null)
  const [newName, setNewName] = useState('')

  const getFileIcon = (mimeType) => {
    if (!mimeType) return <FileIcon size={20} />
    if (mimeType.startsWith('image/')) return <Image size={20} />
    if (mimeType.startsWith('video/')) return <Film size={20} />
    if (mimeType.startsWith('audio/')) return <Music size={20} />
    if (mimeType.includes('text') || mimeType.includes('pdf')) return <FileText size={20} />
    return <FileIcon size={20} />
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleContextMenu = (e, item) => {
    e.preventDefault()
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      item
    })
  }

  const handleRename = (item) => {
    setRenamingItem(item)
    setNewName(item.filename || item.folder_name)
    setContextMenu(null)
  }

  const handleRenameSubmit = () => {
    if (renamingItem && newName.trim()) {
      if (renamingItem.file_id) {
        onFileRename(renamingItem.file_id, newName.trim())
      }
      setRenamingItem(null)
      setNewName('')
    }
  }

  const handleToggleFavorite = async (file) => {
    try {
      await api.post(`/favorites/toggle/${file.file_id}`)
      toast.success(file.is_favorite ? 'Removed from favorites' : 'Added to favorites')
      window.location.reload() // Simple refresh, zou beter zijn met state management
    } catch (error) {
      toast.error('Failed to toggle favorite')
    }
    closeContextMenu()
  }

  const closeContextMenu = () => {
    setContextMenu(null)
  }

  React.useEffect(() => {
    document.addEventListener('click', closeContextMenu)
    return () => document.removeEventListener('click', closeContextMenu)
  }, [])

  if (loading) {
    return (
      <div className="file-browser">
        <div className={`file-grid ${viewMode}`}>
          {[...Array(8)].map((_, i) => (
            <div key={i} className="file-item skeleton" style={{ height: '120px' }} />
          ))}
        </div>
      </div>
    )
  }

  if (files.length === 0 && folders.length === 0) {
    return (
      <div className="file-browser">
        <div className="empty-state">
          <Folder size={64} className="empty-icon" />
          <h3>No files yet</h3>
          <p>Upload files or create folders to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="file-browser">
      <div className={`file-grid ${viewMode}`}>
        {/* Folders */}
        {folders.map(folder => (
          <div
            key={`folder-${folder.folder_id}`}
            className="file-item folder-item"
            onClick={() => onFolderClick(folder.folder_id)}
            onContextMenu={(e) => handleContextMenu(e, folder)}
          >
            <div className="file-icon">
              <Folder size={viewMode === 'grid' ? 48 : 24} />
            </div>
            <div className="file-info">
              <p className="file-name">{folder.folder_name}</p>
              {viewMode === 'list' && (
                <>
                  <p className="file-meta">Folder</p>
                  <p className="file-meta">{format(new Date(folder.created_at), 'MMM dd, yyyy')}</p>
                </>
              )}
            </div>
            <button 
              className="file-menu-btn"
              onClick={(e) => {
                e.stopPropagation()
                handleContextMenu(e, folder)
              }}
            >
              <MoreVertical size={18} />
            </button>
          </div>
        ))}

        {/* Files */}
        {files.map(file => (
          <div
            key={`file-${file.file_id}`}
            className="file-item"
            onClick={() => onFileClick(file)}
            onContextMenu={(e) => handleContextMenu(e, file)}
          >
            {file.thumbnail_path ? (
              <img
                src={`/api/thumbnails/${file.thumbnail_path}`}
                alt={file.filename}
                className="file-thumbnail"
              />
            ) : (
              <div className="file-icon">
                {getFileIcon(file.mime_type)}
              </div>
            )}
            <div className="file-info">
              {renamingItem?.file_id === file.file_id ? (
                <input
                  type="text"
                  className="input rename-input"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onBlur={handleRenameSubmit}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameSubmit()
                    if (e.key === 'Escape') setRenamingItem(null)
                  }}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <p className="file-name" title={file.filename}>
                  {file.is_favorite && <Star size={14} className="favorite-icon" fill="currentColor" />}
                  {file.filename}
                </p>
              )}
              {viewMode === 'list' && (
                <>
                  <p className="file-meta">{formatBytes(file.file_size)}</p>
                  <p className="file-meta">{format(new Date(file.modified_at), 'MMM dd, yyyy')}</p>
                </>
              )}
            </div>
            <button 
              className="file-menu-btn"
              onClick={(e) => {
                e.stopPropagation()
                handleContextMenu(e, file)
              }}
            >
              <MoreVertical size={18} />
            </button>
          </div>
        ))}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="context-menu"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          {contextMenu.item.file_id ? (
            <>
              <div 
                className="context-menu-item"
                onClick={() => {
                  onFileClick(contextMenu.item)
                  closeContextMenu()
                }}
              >
                <Eye size={18} />
                Preview
              </div>
              <div 
                className="context-menu-item"
                onClick={() => handleToggleFavorite(contextMenu.item)}
              >
                <Star size={18} />
                {contextMenu.item.is_favorite ? 'Remove from Favorites' : 'Add to Favorites'}
              </div>
              <div 
                className="context-menu-item"
                onClick={() => {
                  onFileDownload(contextMenu.item)
                  closeContextMenu()
                }}
              >
                <Download size={18} />
                Download
              </div>
              <div 
                className="context-menu-item"
                onClick={() => handleRename(contextMenu.item)}
              >
                <Edit size={18} />
                Rename
              </div>
              <div 
                className="context-menu-item"
                onClick={() => {
                  onFileShare(contextMenu.item)
                  closeContextMenu()
                }}
              >
                <Share2 size={18} />
                Share
              </div>
              <div className="context-menu-divider" />
              <div 
                className="context-menu-item danger"
                onClick={() => {
                  onFileDelete(contextMenu.item.file_id)
                  closeContextMenu()
                }}
              >
                <Trash2 size={18} />
                Delete
              </div>
            </>
          ) : (
            <>
              <div 
                className="context-menu-item"
                onClick={() => {
                  onFolderClick(contextMenu.item.folder_id)
                  closeContextMenu()
                }}
              >
                <Folder size={18} />
                Open
              </div>
              <div className="context-menu-divider" />
              <div 
                className="context-menu-item danger"
                onClick={() => {
                  onFolderDelete(contextMenu.item.folder_id)
                  closeContextMenu()
                }}
              >
                <Trash2 size={18} />
                Delete
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default FileBrowser
