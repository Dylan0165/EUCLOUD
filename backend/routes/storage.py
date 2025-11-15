from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import get_db, User, File
from auth import get_current_user

router = APIRouter()

@router.get("/usage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "storage_used": current_user.storage_used,
        "storage_quota": current_user.storage_quota,
        "storage_available": current_user.storage_quota - current_user.storage_used,
        "usage_percentage": (current_user.storage_used / current_user.storage_quota * 100) if current_user.storage_quota > 0 else 0
    }

@router.get("/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = db.query(
        File.mime_type,
        func.count(File.file_id).label('count'),
        func.sum(File.file_size).label('total_size')
    ).filter_by(
        owner_id=current_user.user_id,
        is_deleted=False
    ).group_by(File.mime_type).all()
    
    file_types = []
    for mime_type, count, total_size in stats:
        file_types.append({
            "mime_type": mime_type or "unknown",
            "count": count,
            "total_size": total_size or 0
        })
    
    total_files = db.query(File).filter_by(owner_id=current_user.user_id, is_deleted=False).count()
    
    return {
        "total_files": total_files,
        "file_types": file_types
    }
