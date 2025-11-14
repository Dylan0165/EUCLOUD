# EUCLOUD - Personal Cloud Storage Platform

A full-stack cloud storage application similar to Google Drive, built with React and Flask.

## 🚀 Features

### File Management
- ✅ Upload files (single & bulk) with drag & drop
- ✅ Download files (single & bulk as zip)
- ✅ Delete files with confirmation
- ✅ Rename files inline
- ✅ Move files between folders
- ✅ Copy files
- ✅ Real-time search

### Folder Management
- ✅ Create nested folder structure
- ✅ Navigate through folders with breadcrumbs
- ✅ Rename folders
- ✅ Delete empty folders
- ✅ Sidebar navigation

### File Preview
- ✅ Image preview (jpg, png, gif)
- ✅ PDF viewer (inline)
- ✅ Text file viewer (txt, md, json)
- ✅ Video player (mp4, webm)
- ✅ Audio player (mp3, wav)

### Sharing & Permissions
- ✅ Generate share links
- ✅ Public/private toggle
- ✅ Expiration dates for shares
- ✅ Password protection
- ✅ View-only vs Edit permissions

### UI/UX
- ✅ Grid and List view modes
- ✅ Dark mode toggle
- ✅ Responsive design (mobile + desktop)
- ✅ Context menus (right-click)
- ✅ Toast notifications
- ✅ Loading skeletons
- ✅ Progress bars for uploads

### Storage
- ✅ 5GB storage quota per user
- ✅ Storage usage tracking
- ✅ File versioning support

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database
- **SQLite** - Database
- **Flask-JWT-Extended** - Authentication
- **Flask-CORS** - Cross-origin requests
- **Pillow** - Image processing
- **Werkzeug** - Security utilities

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client
- **Lucide React** - Icons
- **React Dropzone** - File upload
- **React Toastify** - Notifications
- **date-fns** - Date formatting

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to backend folder:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file (copy from `.env.example`):
```bash
copy .env.example .env
```

6. Run the Flask server:
```bash
python app.py
```

Backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend folder:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

## 🗄️ Database Schema

### Users
- user_id (Primary Key)
- email (Unique)
- password_hash
- storage_quota (5GB default)
- storage_used
- created_at

### Files
- file_id (Primary Key)
- filename
- file_path
- file_size
- mime_type
- folder_id (Foreign Key)
- owner_id (Foreign Key)
- thumbnail_path
- is_deleted
- created_at
- modified_at

### Folders
- folder_id (Primary Key)
- folder_name
- parent_folder_id (Foreign Key - self-referencing)
- owner_id (Foreign Key)
- created_at

### Shares
- share_id (Primary Key)
- file_id (Foreign Key)
- created_by (Foreign Key)
- access_type ('view' or 'edit')
- password_hash
- expires_at
- created_at

### File Versions
- version_id (Primary Key)
- file_id (Foreign Key)
- version_number
- file_path
- file_size
- created_at

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
```

### Files
```
POST   /api/files/upload
GET    /api/files/list?folder_id=123
GET    /api/files/{file_id}
GET    /api/files/{file_id}/download
PUT    /api/files/{file_id}/rename
DELETE /api/files/{file_id}
POST   /api/files/{file_id}/move
POST   /api/files/{file_id}/copy
GET    /api/files/{file_id}/preview
```

### Folders
```
POST   /api/folders/create
GET    /api/folders/list
GET    /api/folders/{folder_id}
PUT    /api/folders/{folder_id}/rename
DELETE /api/folders/{folder_id}
```

### Sharing
```
POST   /api/share/create
GET    /api/share/{share_id}
DELETE /api/share/{share_id}
```

### Storage
```
GET    /api/storage/usage
GET    /api/storage/stats
```

## 🎨 Screenshots

(Add screenshots here)

## 🔒 Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- Protected routes
- CORS configuration
- File type validation
- Storage quota enforcement

## 🚧 Future Enhancements

- [ ] File versioning UI
- [ ] Trash/Recycle bin
- [ ] Batch operations
- [ ] Advanced search filters
- [ ] File tags and categories
- [ ] Collaborative editing
- [ ] Integration with EUWord (document editor)
- [ ] Mobile apps (iOS/Android)

## 📝 License

MIT License

## 👤 Author

Dylan - EUCLOUD Project

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

Built with ❤️ using React & Flask
