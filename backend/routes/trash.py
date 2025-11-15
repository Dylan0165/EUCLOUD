from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from models import get_db, File, User, Activity
from auth import get_current_user

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

@router.get("/list")
async def list_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deleted_files = db.query(File).filter_by(
        owner_id=current_user.user_id,
        is_deleted=True
    ).order_by(File.deleted_at.desc()).all()
    
    return {
        "files": [f.to_dict() for f in deleted_files]
    }

@router.post("/restore/{file_id}")
async def restore_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file.is_deleted:
        raise HTTPException(status_code=400, detail="File is not in trash")
    
    file.is_deleted = False
    file.deleted_at = None
    
    current_user.storage_used += file.file_size
    
    log_activity(db, current_user.user_id, "restore", file_id=file_id, details=f"Restored {file.filename}")
    
    try:
        db.commit()
        
        return {
            "message": "File restored successfully",
            "file": file.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/permanent/{file_id}")
async def delete_permanently(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import os
    from config import Config
    
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file.is_deleted:
        raise HTTPException(status_code=400, detail="File must be in trash first")
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    if file.thumbnail_path:
        thumb_path = os.path.join(Config.THUMBNAIL_FOLDER, file.thumbnail_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    
    try:
        db.delete(file)
        db.commit()
        
        return {"message": "File permanently deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/empty")
async def empty_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import os
    from config import Config
    
    deleted_files = db.query(File).filter_by(
        owner_id=current_user.user_id,
        is_deleted=True
    ).all()
    
    for file in deleted_files:
        file_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if file.thumbnail_path:
            thumb_path = os.path.join(Config.THUMBNAIL_FOLDER, file.thumbnail_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
        db.delete(file)
    
    try:
        db.commit()
        
        return {
            "message": f"Deleted {len(deleted_files)} files permanently",
            "count": len(deleted_files)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
