import React from 'react'
import { Folder, Home, Star } from 'lucide-react'
import './Sidebar.css'

function Sidebar({ folders, currentFolder, onFolderClick, onShowFavorites }) {
  // Build folder tree structure
  const buildFolderTree = () => {
    const rootFolders = folders.filter(f => !f.parent_folder_id)
    return rootFolders.map(folder => ({
      ...folder,
      children: folders.filter(f => f.parent_folder_id === folder.folder_id)
    }))
  }

  const folderTree = buildFolderTree()

  const FolderItem = ({ folder, level = 0 }) => (
    <div>
      <div
        className={`sidebar-item ${currentFolder === folder.folder_id ? 'active' : ''}`}
        onClick={() => onFolderClick(folder.folder_id)}
        style={{ paddingLeft: `${16 + level * 16}px` }}
      >
        <Folder size={18} />
        <span>{folder.folder_name}</span>
      </div>
      {folder.children?.map(child => (
        <FolderItem key={child.folder_id} folder={child} level={level + 1} />
      ))}
    </div>
  )

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h3 className="sidebar-title">Quick Access</h3>
        <div
          className={`sidebar-item ${!currentFolder ? 'active' : ''}`}
          onClick={() => onFolderClick(null)}
        >
          <Home size={18} />
          <span>My Files</span>
        </div>
        
        <div
          className="sidebar-item"
          onClick={onShowFavorites}
        >
          <Star size={18} />
          <span>Favorites</span>
        </div>
      </div>

      {folderTree.length > 0 && (
        <div className="sidebar-section">
          <h3 className="sidebar-title">Folders</h3>
          {folderTree.map(folder => (
            <FolderItem key={folder.folder_id} folder={folder} />
          ))}
        </div>
      )}
    </aside>
  )
}

export default Sidebar
