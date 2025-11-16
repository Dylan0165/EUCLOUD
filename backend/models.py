"""
SQLAlchemy models for FastAPI
Pure SQLAlchemy implementation (no Flask-SQLAlchemy)
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
import os

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./instance/eucloud.db')

# Create instance directory if it doesn't exist
os.makedirs('./instance', exist_ok=True)

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Dependency to get database session
def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Models
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    storage_quota = Column(BigInteger, default=5368709120)  # 5GB
    storage_used = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    files = relationship('File', back_populates='owner', cascade='all, delete-orphan')
    folders = relationship('Folder', back_populates='owner', cascade='all, delete-orphan')
    shares = relationship('Share', back_populates='creator', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password - truncate to 72 bytes for bcrypt"""
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')
        self.password_hash = pwd_context.hash(password_truncated)
    
    def check_password(self, password):
        """Verify password - truncate to 72 bytes for bcrypt"""
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(password_truncated, self.password_hash)
    
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


class Folder(Base):
    __tablename__ = 'folders'
    
    folder_id = Column(Integer, primary_key=True)
    folder_name = Column(String(255), nullable=False)
    parent_folder_id = Column(Integer, ForeignKey('folders.folder_id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='folders')
    files = relationship('File', back_populates='folder', cascade='all, delete-orphan')
    
    def to_dict(self, include_children=False, db_session=None):
        """Convert to dictionary"""
        result = {
            'id': self.folder_id,
            'folder_id': self.folder_id,
            'folder_name': self.folder_name,
            'parent_folder_id': self.parent_folder_id,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'type': 'folder'
        }
        
        if include_children and db_session:
            subfolders = db_session.query(Folder).filter(Folder.parent_folder_id == self.folder_id).all()
            result['subfolders'] = [f.to_dict() for f in subfolders]
            result['files'] = [f.to_dict() for f in self.files]
        
        return result


class File(Base):
    __tablename__ = 'files'
    
    file_id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    folder_id = Column(Integer, ForeignKey('folders.folder_id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    thumbnail_path = Column(Text)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='files')
    folder = relationship('Folder', back_populates='files')
    shares = relationship('Share', back_populates='file', cascade='all, delete-orphan')
    versions = relationship('FileVersion', back_populates='file', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        data = {
            'id': self.file_id,
            'file_id': self.file_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'size': self.file_size,
            'mime_type': self.mime_type,
            'folder_id': self.folder_id,
            'owner_id': self.owner_id,
            'thumbnail_path': self.thumbnail_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.modified_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'type': 'file'
        }
        
        if self.is_deleted is not None:
            data['is_deleted'] = self.is_deleted
        if self.deleted_at:
            data['deleted_at'] = self.deleted_at.isoformat()
        if self.is_favorite is not None:
            data['is_favorite'] = self.is_favorite
            
        return data


class Share(Base):
    __tablename__ = 'shares'
    
    share_id = Column(String(50), primary_key=True)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    access_type = Column(String(20), default='view')
    password_hash = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship('User', back_populates='shares')
    file = relationship('File', back_populates='shares')
    
    def set_password(self, password):
        """Hash and set password"""
        if password:
            self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return True
        return pwd_context.verify(password, self.password_hash)
    
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


class FileVersion(Base):
    __tablename__ = 'file_versions'
    
    version_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship('File', back_populates='versions')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'version_id': self.version_id,
            'file_id': self.file_id,
            'version_number': self.version_number,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat()
        }


class Activity(Base):
    __tablename__ = 'activities'
    
    activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=True)
    folder_id = Column(Integer, ForeignKey('folders.folder_id'), nullable=True)
    activity_type = Column(String(50), nullable=False)
    activity_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self, db_session=None):
        data = {
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'folder_id': self.folder_id,
            'activity_type': self.activity_type,
            'activity_details': self.activity_details,
            'created_at': self.created_at.isoformat()
        }
        if db_session:
            user = db_session.query(User).filter(User.user_id == self.user_id).first()
            data['user_email'] = user.email if user else None
        return data


class Tag(Base):
    __tablename__ = 'tags'
    
    tag_id = Column(Integer, primary_key=True)
    tag_name = Column(String(50), nullable=False)
    color = Column(String(7), default='#667eea')
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'tag_name': self.tag_name,
            'color': self.color,
            'created_at': self.created_at.isoformat()
        }


class FileTag(Base):
    __tablename__ = 'file_tags'
    
    file_tag_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.tag_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    __tablename__ = 'comments'
    
    comment_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    comment_text = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('comments.comment_id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self, db_session=None, include_user=True):
        data = {
            'comment_id': self.comment_id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'comment_text': self.comment_text,
            'parent_comment_id': self.parent_comment_id,
            'created_at': self.created_at.isoformat()
        }
        if include_user and db_session:
            user = db_session.query(User).filter(User.user_id == self.user_id).first()
            data['user_email'] = user.email if user else None
        return data
