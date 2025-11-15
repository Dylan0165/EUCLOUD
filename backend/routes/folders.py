from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from models import get_db, Folder, File, User
from auth import get_current_user

router = APIRouter()

class FolderCreate(BaseModel):
    folder_name: str
    parent_folder_id: Optional[int] = None

class FolderRename(BaseModel):
    folder_name: str

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if folder_data.parent_folder_id:
        parent = db.query(Folder).get(folder_data.parent_folder_id)
        if not parent or parent.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Invalid parent folder")
    
    folder = Folder(
        folder_name=folder_data.folder_name,
        parent_folder_id=folder_data.parent_folder_id,
        owner_id=current_user.user_id
    )
    
    try:
        db.add(folder)
        db.commit()
        db.refresh(folder)
        
        return {
            "message": "Folder created successfully",
            "folder": folder.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folders = db.query(Folder).filter_by(owner_id=current_user.user_id).all()
    
    return {
        "folders": [f.to_dict() for f in folders]
    }

@router.get("/{folder_id}")
async def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).get(folder_id)
    
    if not folder or folder.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {
        "folder": folder.to_dict(include_children=True)
    }

@router.put("/{folder_id}/rename")
async def rename_folder(
    folder_id: int,
    folder_data: FolderRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).get(folder_id)
    
    if not folder or folder.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folder.folder_name = folder_data.folder_name
    
    try:
        db.commit()
        
        return {
            "message": "Folder renamed successfully",
            "folder": folder.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).get(folder_id)
    
    if not folder or folder.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    has_files = db.query(File).filter_by(folder_id=folder_id, is_deleted=False).first()
    has_subfolders = db.query(Folder).filter_by(parent_folder_id=folder_id).first()
    
    if has_files or has_subfolders:
        raise HTTPException(status_code=400, detail="Folder is not empty")
    
    try:
        db.delete(folder)
        db.commit()
        
        return {"message": "Folder deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
