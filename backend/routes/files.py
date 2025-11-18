import os
import uuid
import mimetypes
import zipfile
import io
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image

from models import get_db, File, User, Folder, Activity
from auth import get_current_user
from config import Config

router = APIRouter()

def log_activity(db: Session, user_id: int, activity_type: str, file_id: Optional[int] = None, folder_id: Optional[int] = None, details: Optional[str] = None):
    activity = Activity(
        user_id=user_id,
        file_id=file_id,
        folder_id=folder_id,
        activity_type=activity_type,
        activity_details=details
    )
    db.add(activity)

def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def generate_thumbnail(file_path: str, thumbnail_path: str) -> Optional[str]:
    try:
        img = Image.open(file_path)
        img.thumbnail((200, 200))
        img.save(thumbnail_path)
        return thumbnail_path
    except:
        return None

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[int] = Form(None),
    app_type: str = Form('generic'),  # NEW: 'generic', 'eutype', 'eusheets'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No selected file")
        
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        contents = await file.read()
        file_size = len(contents)
        
        if current_user.storage_used + file_size > current_user.storage_quota:
            raise HTTPException(status_code=413, detail="Storage quota exceeded")
        
        if folder_id:
            folder = db.query(Folder).get(folder_id)
            if not folder or folder.owner_id != current_user.user_id:
                raise HTTPException(status_code=403, detail="Invalid folder")
        
        # NEW: User-based directory structure
        user_upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(current_user.user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_file_id = str(uuid.uuid4())
        unique_filename = f"{unique_file_id}.{file_ext}" if file_ext else unique_file_id
        
        # NEW: Store as uploads/{owner_id}/{file_id}.ext
        file_path = os.path.join(user_upload_dir, unique_filename)
        relative_path = f"{current_user.user_id}/{unique_filename}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        mime_type = mimetypes.guess_type(filename)[0]
        
        thumbnail_path = None
        if mime_type and mime_type.startswith('image/'):
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_full_path = os.path.join(Config.THUMBNAIL_FOLDER, thumbnail_filename)
            if generate_thumbnail(file_path, thumbnail_full_path):
                thumbnail_path = thumbnail_filename
        
        new_file = File(
            filename=filename,
            file_path=relative_path,  # NEW: Store relative path
            file_size=file_size,
            mime_type=mime_type,
            folder_id=folder_id,
            owner_id=current_user.user_id,
            app_type=app_type,  # NEW: Store app type
            thumbnail_path=thumbnail_path
        )
        
        db.add(new_file)
        current_user.storage_used += file_size
        
        log_activity(db, current_user.user_id, 'upload', file_id=new_file.file_id, details=f'Uploaded {filename}')
        
        db.commit()
        db.refresh(new_file)
        
        return {
            "message": "File uploaded successfully",
            "file": new_file.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_files(
    folder_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(File).filter_by(owner_id=current_user.user_id, is_deleted=False)
    
    if folder_id:
        query = query.filter_by(folder_id=folder_id)
    else:
        query = query.filter_by(folder_id=None)
    
    files = query.all()
    
    folder_query = db.query(Folder).filter_by(owner_id=current_user.user_id)
    if folder_id:
        folder_query = folder_query.filter_by(parent_folder_id=folder_id)
    else:
        folder_query = folder_query.filter_by(parent_folder_id=None)
    
    folders = folder_query.all()
    
    return {
        "files": [f.to_dict() for f in files],
        "folders": [f.to_dict() for f in folders]
    }

@router.get("/{file_id:int}")
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"file": file.to_dict()}

@router.get("/{file_id:int}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    log_activity(db, current_user.user_id, 'download', file_id=file.file_id, details=f'Downloaded {file.filename}')
    db.commit()
    
    return FileResponse(
        path=file_path,
        filename=file.filename,
        media_type=file.mime_type or 'application/octet-stream'
    )

@router.put("/{file_id:int}/rename")
async def rename_file(
    file_id: int,
    new_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not new_name or not allowed_file(new_name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    old_name = file.filename
    file.filename = new_name
    
    log_activity(db, current_user.user_id, 'rename', file_id=file.file_id, details=f'Renamed {old_name} to {new_name}')
    
    db.commit()
    
    return {
        "message": "File renamed successfully",
        "file": file.to_dict()
    }

@router.delete("/{file_id:int}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.is_deleted = True
    file.deleted_at = datetime.utcnow()
    
    log_activity(db, current_user.user_id, 'delete', file_id=file.file_id, details=f'Deleted {file.filename}')
    
    db.commit()
    
    return {"message": "File moved to trash"}

@router.post("/{file_id:int}/move")
async def move_file(
    file_id: int,
    target_folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if target_folder_id:
        folder = db.query(Folder).get(target_folder_id)
        if not folder or folder.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Invalid target folder")
    
    file.folder_id = target_folder_id
    
    log_activity(db, current_user.user_id, 'move', file_id=file.file_id, details=f'Moved {file.filename}')
    
    db.commit()
    
    return {
        "message": "File moved successfully",
        "file": file.to_dict()
    }

@router.post("/{file_id:int}/copy")
async def copy_file(
    file_id: int,
    target_folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    original_file = db.query(File).get(file_id)
    
    if not original_file or original_file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if target_folder_id:
        folder = db.query(Folder).get(target_folder_id)
        if not folder or folder.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Invalid target folder")
    
    if current_user.storage_used + original_file.file_size > current_user.storage_quota:
        raise HTTPException(status_code=413, detail="Storage quota exceeded")
    
    original_path = os.path.join(Config.UPLOAD_FOLDER, original_file.file_path)
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Original file not found on disk")
    
    unique_filename = f"{uuid.uuid4()}_{original_file.filename}"
    new_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    shutil.copy2(original_path, new_path)
    
    new_file = File(
        filename=f"Copy of {original_file.filename}",
        file_path=unique_filename,
        file_size=original_file.file_size,
        mime_type=original_file.mime_type,
        folder_id=target_folder_id,
        owner_id=current_user.user_id
    )
    
    db.add(new_file)
    current_user.storage_used += original_file.file_size
    
    log_activity(db, current_user.user_id, 'copy', file_id=new_file.file_id, details=f'Copied {original_file.filename}')
    
    db.commit()
    db.refresh(new_file)
    
    return {
        "message": "File copied successfully",
        "file": new_file.to_dict()
    }

@router.get("/{file_id:int}/preview")
async def preview_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.thumbnail_path:
        thumbnail_full_path = os.path.join(Config.THUMBNAIL_FOLDER, file.thumbnail_path)
        if os.path.exists(thumbnail_full_path):
            return FileResponse(
                path=thumbnail_full_path,
                media_type='image/jpeg'
            )
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type=file.mime_type or 'application/octet-stream'
        )
    
    raise HTTPException(status_code=404, detail="File not found on disk")

# NEW: Content endpoints for EuType integration
@router.get("/{file_id:int}/content")
async def get_file_content(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the raw content of a file as text/JSON.
    Used by EuType for document editing.
    """
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        log_activity(db, current_user.user_id, 'read_content', file_id=file.file_id, details=f'Read content of {file.filename}')
        db.commit()
        
        return {
            "file_id": file.file_id,
            "filename": file.filename,
            "content": content,
            "app_type": file.app_type,
            "modified_at": file.modified_at.isoformat() if file.modified_at else None
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not text-based")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.put("/{file_id:int}/content")
async def update_file_content(
    file_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the raw content of a file.
    Used by EuType for saving document changes.
    """
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    try:
        # Calculate size difference for quota management
        old_size = file.file_size
        new_size = len(content.encode('utf-8'))
        size_diff = new_size - old_size
        
        # Check quota
        if current_user.storage_used + size_diff > current_user.storage_quota:
            raise HTTPException(status_code=413, detail="Storage quota exceeded")
        
        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update file metadata
        file.file_size = new_size
        file.modified_at = datetime.utcnow()
        current_user.storage_used += size_diff
        
        log_activity(db, current_user.user_id, 'update_content', file_id=file.file_id, details=f'Updated content of {file.filename}')
        
        db.commit()
        db.refresh(file)
        
        return {
            "message": "File content updated successfully",
            "file": file.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating file: {str(e)}")
