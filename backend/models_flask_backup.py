from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Extended models
class Tag(db.Model):
    __tablename__ = 'tags'
    
    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#667eea')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'tag_name': self.tag_name,
            'color': self.color,
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
    
    def to_dict(self, include_user=True):
        data = {
            'comment_id': self.comment_id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'comment_text': self.comment_text,
            'parent_comment_id': self.parent_comment_id,
            'created_at': self.created_at.isoformat()
        }
        if include_user:
            user = User.query.get(self.user_id)
            data['user_email'] = user.email if user else None
        return data


class Activity(db.Model):
    __tablename__ = 'activities'
    
    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    activity_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        user = User.query.get(self.user_id)
        return {
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'user_email': user.email if user else None,
            'file_id': self.file_id,
            'folder_id': self.folder_id,
            'activity_type': self.activity_type,
            'activity_details': self.activity_details,
            'created_at': self.created_at.isoformat()
        }


class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    storage_quota = db.Column(db.BigInteger, default=5368709120)  # 5GB
    storage_used = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    files = db.relationship('File', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    shares = db.relationship('Share', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'storage_quota': self.storage_quota,
            'storage_used': self.storage_used,
            'storage_available': self.storage_quota - self.storage_used,
            'created_at': self.created_at.isoformat()
        }


class Folder(db.Model):
    __tablename__ = 'folders'
    
    folder_id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String(255), nullable=False)
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    files = db.relationship('File', backref='folder', lazy='dynamic', cascade='all, delete-orphan')
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[folder_id]), lazy='dynamic')
    
    def to_dict(self, include_children=False):
        """Convert to dictionary"""
        result = {
            'id': self.folder_id,  # Add 'id' for compatibility
            'folder_id': self.folder_id,
            'folder_name': self.folder_name,
            'parent_folder_id': self.parent_folder_id,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'type': 'folder'
        }
        
        if include_children:
            result['subfolders'] = [f.to_dict() for f in self.subfolders.all()]
            result['files'] = [f.to_dict() for f in self.files.all()]
        
        return result


class File(db.Model):
    __tablename__ = 'files'
    
    file_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100))
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    thumbnail_path = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shares = db.relationship('Share', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    versions = db.relationship('FileVersion', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        data = {
            'id': self.file_id,  # Add 'id' for compatibility
            'file_id': self.file_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'size': self.file_size,  # Add 'size' for compatibility
            'mime_type': self.mime_type,
            'folder_id': self.folder_id,
            'owner_id': self.owner_id,
            'thumbnail_path': self.thumbnail_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.modified_at.isoformat(),  # Add 'updated_at' for compatibility
            'modified_at': self.modified_at.isoformat(),
            'type': 'file'
        }
        
        # Add optional fields if they exist
        if hasattr(self, 'is_deleted'):
            data['is_deleted'] = self.is_deleted
        if hasattr(self, 'deleted_at') and self.deleted_at:
            data['deleted_at'] = self.deleted_at.isoformat()
        if hasattr(self, 'is_favorite'):
            data['is_favorite'] = self.is_favorite
            
        return data


class Share(db.Model):
    __tablename__ = 'shares'
    
    share_id = db.Column(db.String(50), primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    access_type = db.Column(db.String(20), default='view')  # 'view' or 'edit'
    password_hash = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return True
        return check_password_hash(self.password_hash, password)
    
    def is_expired(self):
        """Check if share has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'share_id': self.share_id,
            'file_id': self.file_id,
            'created_by': self.created_by,
            'access_type': self.access_type,
            'has_password': self.password_hash is not None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat()
        }


class FileVersion(db.Model):
    __tablename__ = 'file_versions'
    
    version_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'version_id': self.version_id,
            'file_id': self.file_id,
            'version_number': self.version_number,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat()
        }
