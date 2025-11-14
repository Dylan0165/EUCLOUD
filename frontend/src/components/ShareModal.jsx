import React, { useState } from 'react'
import { shareService } from '../services'
import { toast } from 'react-toastify'
import { X, Link, Copy, Lock, Calendar, Check } from 'lucide-react'
import './ShareModal.css'

function ShareModal({ file, onClose }) {
  const [shareLink, setShareLink] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  
  // Options
  const [accessType, setAccessType] = useState('view')
  const [expiresInDays, setExpiresInDays] = useState('')
  const [password, setPassword] = useState('')
  const [usePassword, setUsePassword] = useState(false)

  const handleCreateShare = async () => {
    setLoading(true)
    try {
      const options = {
        accessType,
        expiresInDays: expiresInDays ? parseInt(expiresInDays) : undefined,
        password: usePassword ? password : undefined
      }

      const result = await shareService.create(file.file_id, options)
      const fullUrl = `${window.location.origin}${result.share_url}`
      setShareLink(fullUrl)
      toast.success('Share link created!')
    } catch (error) {
      toast.error('Failed to create share link')
    } finally {
      setLoading(false)
    }
  }

  const handleCopyLink = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink)
      setCopied(true)
      toast.success('Link copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Share "{file.filename}"</h2>
          <button className="btn-icon" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {!shareLink ? (
            <div className="share-options">
              <div className="form-group">
                <label>Access Type</label>
                <select 
                  className="input"
                  value={accessType}
                  onChange={(e) => setAccessType(e.target.value)}
                >
                  <option value="view">View only</option>
                  <option value="edit">Can edit</option>
                </select>
              </div>

              <div className="form-group">
                <label>
                  <Calendar size={18} />
                  Expiration (optional)
                </label>
                <select 
                  className="input"
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(e.target.value)}
                >
                  <option value="">Never expires</option>
                  <option value="1">1 day</option>
                  <option value="7">7 days</option>
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                </select>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={usePassword}
                    onChange={(e) => setUsePassword(e.target.checked)}
                  />
                  <Lock size={18} />
                  Password protect
                </label>
                
                {usePassword && (
                  <input
                    type="password"
                    className="input"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                )}
              </div>

              <button 
                className="btn btn-primary btn-full"
                onClick={handleCreateShare}
                disabled={loading || (usePassword && !password)}
              >
                {loading ? 'Creating link...' : 'Create Share Link'}
              </button>
            </div>
          ) : (
            <div className="share-result">
              <div className="share-link-container">
                <Link size={20} className="link-icon" />
                <input
                  type="text"
                  className="input share-link-input"
                  value={shareLink}
                  readOnly
                />
                <button 
                  className={`btn ${copied ? 'btn-success' : 'btn-primary'}`}
                  onClick={handleCopyLink}
                >
                  {copied ? (
                    <>
                      <Check size={18} />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy size={18} />
                      Copy
                    </>
                  )}
                </button>
              </div>

              <div className="share-info">
                <p>✓ Link created successfully</p>
                {expiresInDays && (
                  <p>🕐 Expires in {expiresInDays} day{expiresInDays > 1 ? 's' : ''}</p>
                )}
                {usePassword && (
                  <p>🔒 Protected with password</p>
                )}
                <p>👁️ Access: {accessType === 'view' ? 'View only' : 'Can edit'}</p>
              </div>

              <button 
                className="btn btn-secondary btn-full"
                onClick={() => setShareLink(null)}
              >
                Create Another Link
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ShareModal
