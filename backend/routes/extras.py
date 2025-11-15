from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from models import get_db, File, Tag, FileTag, Comment, Activity, User
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

@router.post("/favorites/toggle/{file_id}")
async def toggle_favorite(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.is_favorite = not file.is_favorite
    
    log_activity(
        db,
        current_user.user_id,
        "favorite" if file.is_favorite else "unfavorite",
        file_id=file_id,
        details=f"{'Favorited' if file.is_favorite else 'Unfavorited'} {file.filename}"
    )
    
    try:
        db.commit()
        
        return {
            "message": "Favorite toggled",
            "is_favorite": file.is_favorite
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/favorites/list")
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    favorites = db.query(File).filter_by(
        owner_id=current_user.user_id,
        is_favorite=True,
        is_deleted=False
    ).all()
    
    return {
        "files": [f.to_dict() for f in favorites]
    }

class TagCreate(BaseModel):
    tag_name: str
    color: Optional[str] = None

@router.post("/tags/create", status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Tag).filter_by(
        tag_name=tag_data.tag_name,
        owner_id=current_user.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    tag = Tag(
        tag_name=tag_data.tag_name,
        color=tag_data.color,
        owner_id=current_user.user_id
    )
    
    try:
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        return {
            "message": "Tag created successfully",
            "tag": tag.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tags/list")
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tags = db.query(Tag).filter_by(owner_id=current_user.user_id).all()
    
    return {
        "tags": [t.to_dict() for t in tags]
    }

@router.post("/tags/add/{file_id}/{tag_id}")
async def add_tag_to_file(
    file_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    tag = db.query(Tag).get(tag_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not tag or tag.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    existing = db.query(FileTag).filter_by(file_id=file_id, tag_id=tag_id).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag already added to file")
    
    file_tag = FileTag(file_id=file_id, tag_id=tag_id)
    
    try:
        db.add(file_tag)
        db.commit()
        
        return {"message": "Tag added to file"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tags/remove/{file_id}/{tag_id}")
async def remove_tag_from_file(
    file_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_tag = db.query(FileTag).filter_by(file_id=file_id, tag_id=tag_id).first()
    
    if not file_tag:
        raise HTTPException(status_code=404, detail="Tag not found on file")
    
    try:
        db.delete(file_tag)
        db.commit()
        
        return {"message": "Tag removed from file"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class CommentCreate(BaseModel):
    comment_text: str

@router.post("/comments/{file_id}", status_code=status.HTTP_201_CREATED)
async def add_comment(
    file_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    comment = Comment(
        file_id=file_id,
        user_id=current_user.user_id,
        comment_text=comment_data.comment_text
    )
    
    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        return {
            "message": "Comment added",
            "comment": comment.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comments/{file_id}")
async def get_comments(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(File).get(file_id)
    
    if not file or file.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    comments = db.query(Comment).filter_by(file_id=file_id).order_by(Comment.created_at.desc()).all()
    
    return {
        "comments": [c.to_dict() for c in comments]
    }

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).get(comment_id)
    
    if not comment or comment.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    try:
        db.delete(comment)
        db.commit()
        
        return {"message": "Comment deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity")
async def get_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    activities = db.query(Activity).filter_by(
        user_id=current_user.user_id
    ).order_by(Activity.created_at.desc()).limit(50).all()
    
    return {
        "activities": [a.to_dict() for a in activities]
    }
