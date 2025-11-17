import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { fileService, folderService, storageService } from '../services'
import { toast } from 'react-toastify'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import FileBrowser from '../components/FileBrowser'
import UploadModal from '../components/UploadModal'
import FilePreviewModal from '../components/FilePreviewModal'
import ShareModal from '../components/ShareModal'
import TrashModal from '../components/TrashModal'
import FavoritesView from '../components/FavoritesView'
import './Dashboard.css'

function Dashboard() {
  const { user } = useAuth()
  const [files, setFiles] = useState([])
  const [folders, setFolders] = useState([])
  const [currentFolder, setCurrentFolder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'
  const [searchQuery, setSearchQuery] = useState('')
  const [storageInfo, setStorageInfo] = useState(null)
  
  // Modals
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const [shareFile, setShareFile] = useState(null)
  const [trashModalOpen, setTrashModalOpen] = useState(false)
  const [favoritesViewOpen, setFavoritesViewOpen] = useState(false)

  useEffect(() => {
    loadData()
  }, [currentFolder])

  const loadData = async () => {
    setLoading(true)
    try {
      const [fileData, storageData] = await Promise.all([
        fileService.list(currentFolder),
        storageService.getUsage()
      ])
      
      setFiles(fileData.files || [])
      setFolders(fileData.folders || [])
      setStorageInfo(storageData)
    } catch (error) {
      toast.error('Failed to load data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadComplete = () => {
    setUploadModalOpen(false)
    loadData()
  }

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm('Are you sure you want to delete this file?')) {
      return
    }

    try {
      await fileService.delete(fileId)
      toast.success('File deleted successfully')
      loadData()
    } catch (error) {
      toast.error('Failed to delete file')
    }
  }

  const handleRenameFile = async (fileId, newName) => {
    try {
      await fileService.rename(fileId, newName)
      toast.success('File renamed successfully')
      loadData()
    } catch (error) {
      toast.error('Failed to rename file')
    }
  }

  const handleDownloadFile = async (file) => {
    try {
      await fileService.download(file.file_id, file.filename)
      toast.success('Download started')
    } catch (error) {
      toast.error('Failed to download file')
    }
  }

  const handleCreateFolder = async (folderName) => {
    try {
      await folderService.create(folderName, currentFolder)
      toast.success('Folder created successfully')
      loadData()
    } catch (error) {
      toast.error('Failed to create folder')
    }
  }

  const handleDeleteFolder = async (folderId) => {
    if (!window.confirm('Are you sure you want to delete this folder?')) {
      return
    }

    try {
      await folderService.delete(folderId)
      toast.success('Folder deleted successfully')
      loadData()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to delete folder')
    }
  }

  const handleFolderClick = (folderId) => {
    setCurrentFolder(folderId)
  }

  const handleFilePreview = (file) => {
    setPreviewFile(file)
  }

  const handleShareFile = (file) => {
    setShareFile(file)
  }

  // Filter files and folders based on search
  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredFolders = folders.filter(folder =>
    folder.folder_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="dashboard">
      <Header
        user={user}
        storageInfo={storageInfo}
        onUploadClick={() => setUploadModalOpen(true)}
        onCreateFolder={handleCreateFolder}
        onTrashClick={() => setTrashModalOpen(true)}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      
      <div className="dashboard-content">
        <Sidebar
          folders={folders}
          currentFolder={currentFolder}
          onFolderClick={handleFolderClick}
          onShowFavorites={() => setFavoritesViewOpen(true)}
        />
        
        {/* Welcome message for testing PVC persistence */}
        {!currentFolder && files.length === 0 && !loading && (
          <div style={{
            position: 'absolute',
            top: '150px',
            left: '50%',
            transform: 'translateX(-50%)',
            textAlign: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '30px 50px',
            borderRadius: '15px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
            zIndex: 1000
          }}>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '28px' }}>🎉 Welcome to EUCLOUD!</h2>
            <p style={{ margin: 0, fontSize: '16px', opacity: 0.95 }}>
              Upload your first file to test persistent storage (PVC) ⬆️
            </p>
          </div>
        )}
        
        <FileBrowser
          files={filteredFiles}
          folders={filteredFolders}
          viewMode={viewMode}
          loading={loading}
          currentFolder={currentFolder}
          onFolderClick={handleFolderClick}
          onFileClick={handleFilePreview}
          onFileDownload={handleDownloadFile}
          onFileDelete={handleDeleteFile}
          onFileRename={handleRenameFile}
          onFileShare={handleShareFile}
          onFolderDelete={handleDeleteFolder}
        />
      </div>

      {uploadModalOpen && (
        <UploadModal
          currentFolder={currentFolder}
          onClose={() => setUploadModalOpen(false)}
          onComplete={handleUploadComplete}
        />
      )}

      {previewFile && (
        <FilePreviewModal
          file={previewFile}
          onClose={() => setPreviewFile(null)}
          onDownload={() => handleDownloadFile(previewFile)}
        />
      )}

      {shareFile && (
        <ShareModal
          file={shareFile}
          onClose={() => setShareFile(null)}
        />
      )}

      {trashModalOpen && (
        <TrashModal
          onClose={() => setTrashModalOpen(false)}
          onRestore={loadData}
        />
      )}

      {favoritesViewOpen && (
        <FavoritesView
          onClose={() => setFavoritesViewOpen(false)}
          onFileClick={(file) => {
            setPreviewFile(file)
            setFavoritesViewOpen(false)
          }}
        />
      )}
    </div>
  )
}

export default Dashboard
