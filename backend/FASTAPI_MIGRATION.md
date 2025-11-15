# FastAPI Migration Guide

## ✅ Completed Steps

### 1. Updated requirements.txt
- ✅ Removed Flask, Flask-CORS, Flask-SQLAlchemy, Flask-JWT-Extended
- ✅ Added FastAPI, uvicorn, python-multipart, python-jose, passlib
- ✅ Kept SQLAlchemy and other dependencies

### 2. Created main.py (FastAPI app)
- ✅ Replaced Flask app factory with FastAPI app
- ✅ Added CORS middleware
- ✅ Setup lifespan for database initialization
- ✅ Included all route prefixes (/api/auth, /api/files, etc.)
- ✅ Added global exception handler
- ✅ Configured Swagger docs at /docs

### 3. Created auth.py (JWT module)
- ✅ Replaced Flask-JWT-Extended with python-jose
- ✅ Fixed "Subject must be a string" bug (stores user_id as int)
- ✅ Created `get_current_user` dependency (replaces @jwt_required)
- ✅ Added password hashing with passlib/bcrypt

## 🚧 Remaining Work

### 4. Update models.py
**Status**: Needs to be recreated with SQLAlchemy Core (no Flask-SQLAlchemy)

**Required changes**:
- Replace `db.Model` with `Base` from declarative_base
- Replace `db.Column` with plain `Column`
- Replace `db.relationship` with plain `relationship`
- Add `get_db()` dependency function
- Keep all model logic (to_dict, set_password, etc.)

### 5. Convert all route files
**Files to convert** (keep same endpoints, change implementation):
- routes/auth.py
- routes/files.py
- routes/folders.py  
- routes/shares.py
- routes/storage.py
- routes/trash.py
- routes/extras.py

**For each route file**:
- Replace `Blueprint` with `APIRouter`
- Replace `@bp.route()` with `@router.get()` or `@router.post()`
- Replace `@jwt_required()` with `user: User = Depends(get_current_user)`
- Replace `request.get_json()` with Pydantic models
- Replace `request.files['file']` with `file: UploadFile`
- Replace `jsonify()` with plain dict return
- Make file upload routes `async def`
- Add `db = Depends(get_db)` parameter to all routes

### 6. Create Pydantic schemas
**New file needed**: `schemas.py`

Create schemas for:
- LoginRequest, RegisterRequest
- FileUpload, FileResponse
- FolderCreate, FolderResponse
- ShareCreate, ShareResponse
- etc.

### 7. Update Dockerfile
**Changes needed**:
```dockerfile
# Change CMD from:
CMD ["flask", "run", "--host=0.0.0.0"]

# To:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

### 8. Update config.py
- Remove Flask-specific config
- Keep environment variables and paths
- Ensure `init_app()` works without Flask app

## 📋 Testing Checklist

After migration:
- [ ] /api/auth/register - User registration
- [ ] /api/auth/login - User login (JWT token)
- [ ] /api/auth/me - Get current user (with token)
- [ ] /api/files/upload - File upload
- [ ] /api/files/list - List files
- [ ] /api/folders/create - Create folder
- [ ] /api/storage/usage - Storage stats
- [ ] /api/trash/list - List deleted files

## 🎯 Priority Order

1. **HIGH**: Complete models.py conversion
2. **HIGH**: Convert routes/auth.py (login, register, /me)
3. **MEDIUM**: Convert routes/files.py (upload, list, download)
4. **MEDIUM**: Convert routes/storage.py
5. **LOW**: Convert other routes (folders, shares, trash, extras)
6. **FINAL**: Update Dockerfile and test deployment

## 💡 Quick Tips

- All routes stay at same URLs (e.g., `/api/auth/login`)
- Frontend code doesn't need changes
- Environment variables stay the same
- Database schema stays the same
- Kubernetes configs don't need changes

## 🐛 Common Issues to Watch

1. **async/await**: File operations should be async
2. **Database sessions**: Use `db = Depends(get_db)` everywhere
3. **File uploads**: Use `UploadFile` type hint
4. **Auth**: Use `Depends(get_current_user)` instead of decorator
5. **Returns**: Just return dict, no `jsonify()`

## Next Steps

1. Restore and convert models.py
2. Convert auth routes as example
3. Test auth flow end-to-end
4. Convert remaining routes
5. Update Dockerfile
6. Deploy and test

