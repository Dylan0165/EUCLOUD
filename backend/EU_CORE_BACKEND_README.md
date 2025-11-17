# EU-CORE-BACKEND - Multi-App Backend Service

## Overview

EU-CORE-BACKEND is a FastAPI-based cloud storage backend that serves multiple frontend applications:
- **EuCloud** (Port 30080): File browser and management
- **EuType** (Port 30081): Document editor for .ty files
- **EuSheets** (Future): Spreadsheet editor

## What Changed in v2.0

### 1. Multi-App Architecture
- Added `app_type` field to File model (`generic`, `eutype`, `eusheets`)
- CORS configured for multiple frontend ports (30080, 30081)
- Backend now serves as shared service for all EU apps

### 2. User-Based Storage Structure
**Old**: `/uploads/{uuid}_{filename}`
**New**: `/uploads/{owner_id}/{file_id}.ext`

Benefits:
- User isolation
- Better organization
- Easier backup/migration per user
- Clearer ownership

### 3. Content Endpoints for EuType
New endpoints for direct content read/write:
- `GET /api/files/{id}/content` - Read text content
- `PUT /api/files/{id}/content` - Update text content

These enable real-time document editing in EuType without full file download/upload.

### 4. Enhanced Security
- Argon2 password hashing (replaces bcrypt)
- JWT with 24-hour expiry
- User-specific file access validation

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migration (ONE TIME ONLY)
```bash
python migrate_to_multiapp.py
```

This script:
- Adds `app_type` column to files table
- Migrates existing files to user-based directories
- Sets default app_types based on file extensions

### 3. Start Backend
```bash
python main.py
```

Backend runs on: `http://0.0.0.0:5000`

### 4. Test Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# Upload file
curl -X POST http://localhost:5000/api/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.ty" \
  -F "app_type=eutype"

# Get file content
curl http://localhost:5000/api/files/1/content \
  -H "Authorization: Bearer <token>"
```

## API Documentation

See **[API_CONTRACT.md](../API_CONTRACT.md)** for complete API reference including:
- Authentication (register, login, me)
- File operations (upload, list, download, rename, delete)
- Content endpoints (read, write)
- Storage information
- Error handling
- EuType integration guide

## Architecture

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **Database**: SQLite with SQLAlchemy 2.0.35
- **Auth**: python-jose (JWT), passlib (Argon2)
- **Server**: uvicorn

### Database Models
- **User**: Authentication, quota management
- **File**: File metadata with app_type
- **Folder**: Hierarchical organization
- **Share**: Public share links
- **Activity**: Audit log
- **Tag**, **Comment**, **FileVersion**: Extended features

### Storage Structure
```
backend/
├── uploads/
│   ├── 1/              # User ID 1
│   │   ├── uuid1.ty
│   │   ├── uuid2.pdf
│   │   └── uuid3.png
│   ├── 2/              # User ID 2
│   │   └── uuid4.ty
│   └── ...
├── thumbnails/
│   └── thumb_*.jpg
└── instance/
    └── eucloud.db
```

### File Path Handling
- **Database**: `file_path = "1/uuid.ext"` (relative)
- **Filesystem**: `uploads/1/uuid.ext` (absolute)
- **Original Name**: Stored in `filename` column
- **File ID**: UUID v4 generated on upload

## Multi-App Integration

### App Types
| Type     | Frontend | Port  | File Extensions | Purpose              |
|----------|----------|-------|-----------------|----------------------|
| generic  | EuCloud  | 30080 | All             | File browser         |
| eutype   | EuType   | 30081 | .ty             | Document editor      |
| eusheets | EuSheets | TBD   | .sheet          | Spreadsheet (future) |

### CORS Configuration
```python
allow_origins=[
    "http://192.168.124.50:30080",  # EuCloud
    "http://192.168.124.50:30081",  # EuType
    "http://localhost:5173",         # Development
    "http://localhost:30080",
    "http://localhost:30081"
]
```

### EuType Integration Workflow

1. **User Login** → Get JWT token
2. **List Files** → Filter by `app_type=eutype`
3. **Load Document** → `GET /api/files/{id}/content`
4. **Edit Document** → In-memory changes in EuType
5. **Save Document** → `PUT /api/files/{id}/content`
6. **Create New** → Upload with `app_type=eutype`

## Deployment

### Kubernetes (K3s)
Backend runs as NodePort service on port 30500.

```bash
# Apply Kubernetes configs
kubectl apply -f k8s/

# Check status
kubectl get pods -n eucloud
kubectl logs -f deployment/backend -n eucloud
```

### Docker Compose
```bash
docker-compose up -d backend
```

### Environment Variables
- `SECRET_KEY`: JWT signing key (auto-generated if not set)
- `DATABASE_URL`: SQLite path (default: `sqlite:///instance/eucloud.db`)

## Migration Guide

### From v1.0 (Flask) to v2.0 (FastAPI)

If you have an existing v1.0 installation:

1. **Backup Database**:
   ```bash
   cp backend/instance/eucloud.db backend/instance/eucloud.db.backup
   ```

2. **Backup Uploads**:
   ```bash
   cp -r backend/uploads backend/uploads.backup
   ```

3. **Run Migration**:
   ```bash
   python backend/migrate_to_multiapp.py
   ```

4. **Verify**:
   - Check that files moved to user directories
   - Test file download/upload
   - Test content endpoints with .ty files

5. **Cleanup** (after verification):
   ```bash
   rm -rf backend/uploads.backup
   ```

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI app entry
├── config.py            # Configuration
├── models.py            # SQLAlchemy models
├── auth.py              # JWT authentication
├── routes/              # API endpoints
│   ├── auth.py          # Login, register
│   ├── files.py         # File CRUD + content endpoints
│   ├── folders.py       # Folder management
│   ├── shares.py        # Public shares
│   ├── storage.py       # Quota info
│   ├── trash.py         # Soft delete
│   └── extras.py        # Tags, comments, activity
└── migrate_to_multiapp.py  # Migration script
```

### Adding a New App Type

1. Update `app_type` enum values in documentation
2. Add CORS origin for new frontend port
3. Create app-specific routes if needed (optional)
4. Update file upload form in frontend to set `app_type`

Example:
```python
# main.py
allow_origins=[
    ...,
    "http://192.168.124.50:30082",  # New app
]
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (TODO: create test suite)
pytest
```

## Troubleshooting

### Files Not Found After Migration
- Check `backend/uploads/{user_id}/` directories exist
- Verify database `file_path` column format: `{user_id}/{uuid}.ext`
- Run migration script again (it skips already migrated files)

### CORS Errors from EuType
- Verify EuType runs on port 30081
- Check `main.py` CORS configuration includes port 30081
- Restart backend after CORS changes

### Content Endpoints Return 400
- Ensure file is text-based (not binary)
- Check file exists on disk at `uploads/{file.file_path}`
- Verify user owns the file

### Storage Quota Exceeded
- Check current usage: `GET /api/storage/usage`
- Default quota: 5 GB per user
- Update quota in database if needed:
  ```sql
  UPDATE users SET storage_quota = 10737418240 WHERE user_id = 1;
  ```

## Security Considerations

- **Passwords**: Hashed with Argon2 (memory-hard, resistant to GPU attacks)
- **JWT**: 24-hour expiry, signed with SECRET_KEY
- **File Access**: Owner validation on all operations
- **Quota**: Enforced on upload and content updates
- **CORS**: Restricted to specific origins (no wildcard in production)

## Performance

- **File Uploads**: Streamed to disk (no memory buffering)
- **Content Endpoints**: Direct file I/O (efficient for small .ty files)
- **Database**: SQLite (suitable for single-server deployments)
- **Thumbnails**: Generated async for images only

## Future Enhancements

- [ ] WebSocket support for real-time collaboration
- [ ] File versioning for content endpoint updates
- [ ] Shared folder permissions
- [ ] Admin panel for quota management
- [ ] PostgreSQL support for multi-server deployments
- [ ] S3-compatible object storage backend
- [ ] Rate limiting per user

## Contributing

1. Create feature branch from `main`
2. Make changes with clear commit messages
3. Update API_CONTRACT.md if adding endpoints
4. Test with all frontends (EuCloud, EuType)
5. Submit pull request

## License

[Your License Here]

## Support

For issues or questions:
- Check API_CONTRACT.md for API documentation
- Review QUICK_REFERENCE.md for common tasks
- Contact backend development team

---

**Version**: 2.0.0  
**Last Updated**: 2024-01-15  
**Maintained By**: Backend Team
