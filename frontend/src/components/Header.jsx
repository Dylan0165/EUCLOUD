import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { 
  Cloud, Upload, FolderPlus, Search, Grid, List, 
  Moon, Sun, LogOut, User, HardDrive, Trash2
} from 'lucide-react'
import './Header.css'

function Header({ 
  user, 
  storageInfo, 
  onUploadClick, 
  onCreateFolder,
  onTrashClick,
  viewMode,
  onViewModeChange,
  searchQuery,
  onSearchChange
}) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [darkMode, setDarkMode] = useState(false)
  const [showCreateFolder, setShowCreateFolder] = useState(false)
  const [folderName, setFolderName] = useState('')
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    document.documentElement.setAttribute('data-theme', !darkMode ? 'dark' : 'light')
  }

  const handleCreateFolder = (e) => {
    e.preventDefault()
    if (folderName.trim()) {
      onCreateFolder(folderName.trim())
      setFolderName('')
      setShowCreateFolder(false)
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
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <Cloud size={28} />
            <span>EUCLOUD</span>
          </div>
          
          <div className="search-bar">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
        </div>

        <div className="header-right">
          <div className="header-actions">
            <button className="btn btn-primary" onClick={onUploadClick}>
              <Upload size={18} />
              Upload
            </button>
            
            <button 
              className="btn btn-secondary" 
              onClick={() => setShowCreateFolder(true)}
            >
              <FolderPlus size={18} />
              New Folder
            </button>

            <button 
              className="btn btn-secondary" 
              onClick={onTrashClick}
              title="Trash"
            >
              <Trash2 size={18} />
              Trash
            </button>

            <div className="view-toggle">
              <button
                className={`btn-icon ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => onViewModeChange('grid')}
                title="Grid view"
              >
                <Grid size={18} />
              </button>
              <button
                className={`btn-icon ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => onViewModeChange('list')}
                title="List view"
              >
                <List size={18} />
              </button>
            </div>

            <button className="btn-icon" onClick={toggleDarkMode} title="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>

          <div className="user-menu">
            <button 
              className="user-button"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <User size={20} />
              <span>{user?.email}</span>
            </button>

            {showUserMenu && (
              <div className="user-dropdown">
                <div className="storage-info">
                  <div className="storage-icon">
                    <HardDrive size={18} />
                  </div>
                  <div className="storage-details">
                    <p className="storage-text">
                      {storageInfo ? formatBytes(storageInfo.storage_used) : '0 B'} / 
                      {storageInfo ? formatBytes(storageInfo.storage_quota) : '5 GB'}
                    </p>
                    <div className="storage-bar">
                      <div 
                        className="storage-bar-fill"
                        style={{ 
                          width: `${storageInfo?.usage_percentage || 0}%` 
                        }}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="context-menu-divider" />
                
                <button className="context-menu-item" onClick={handleLogout}>
                  <LogOut size={18} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {showCreateFolder && (
        <div className="modal-backdrop" onClick={() => setShowCreateFolder(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Folder</h2>
            <form onSubmit={handleCreateFolder}>
              <input
                type="text"
                className="input"
                placeholder="Folder name"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                autoFocus
              />
              <div className="modal-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowCreateFolder(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  )
}

export default Header
