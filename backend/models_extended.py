from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tag(db.Model):
    __tablename__ = 'tags'
    
    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#667eea')  # Hex color
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'tag_name': self.tag_name,
            'color': self.color,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }


class FileTag(db.Model):
    __tablename__ = 'file_tags'
    
    file_tag_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comments'
    
    comment_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[comment_id]), lazy='dynamic')
    
    def to_dict(self):
        return {
            'comment_id': self.comment_id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'comment_text': self.comment_text,
            'parent_comment_id': self.parent_comment_id,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }


class Activity(db.Model):
    __tablename__ = 'activities'
    
    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)  # upload, delete, share, rename, etc.
    activity_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activities')
    
    def to_dict(self):
        return {
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'file_id': self.file_id,
            'folder_id': self.folder_id,
            'activity_type': self.activity_type,
            'activity_details': self.activity_details,
            'created_at': self.created_at.isoformat()
        }
