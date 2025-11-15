import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import get_db, Share, File, User
from auth import get_current_user

router = APIRouter()

class ShareCreate(BaseModel):
    file_id: int
    access_type: str = "view"
    expires_in_days: Optional[int] = None
    password: Optional[str] = None

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_share(
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(share_data.file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    share_id = str(uuid.uuid4())[:12]
    
    expires_at = None
    if share_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)
    
    share = Share(
        share_id=share_id,
        file_id=file.file_id,
        created_by=current_user.user_id,
        access_type=share_data.access_type,
        expires_at=expires_at
    )
    
    if share_data.password:
        share.set_password(share_data.password)
    
    try:
        db.add(share)
        db.commit()
        db.refresh(share)
        
        return {
            "message": "Share created successfully",
            "share": share.to_dict(),
            "share_url": f"/share/{share_id}"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{share_id}")
async def get_share(
    share_id: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    share = db.query(Share).get(share_id)
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share.is_expired():
        raise HTTPException(status_code=410, detail="Share has expired")
    
    if share.password_hash and not share.check_password(password):
        return {
            "error": "Password required",
            "requires_password": True
        }
    
    file = db.query(File).get(share.file_id)
    
    return {
        "share": share.to_dict(),
        "file": file.to_dict()
    }

@router.delete("/{share_id}")
async def delete_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    share = db.query(Share).get(share_id)
    
    if not share or share.created_by != current_user.user_id:
        raise HTTPException(status_code=404, detail="Share not found")
    
    try:
        db.delete(share)
        db.commit()
        
        return {"message": "Share deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
