import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eucloud.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    THUMBNAIL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnails')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB per file
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
                         'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'mp4', 'mp3', 
                         'wav', 'avi', 'mov', 'json', 'md', 'py', 'js', 'html', 'css',
                         'ty'}  # TYPE editor bestanden
    
    # Storage Quotas (in bytes)
    DEFAULT_STORAGE_QUOTA = 5 * 1024 * 1024 * 1024  # 5GB
    
    @staticmethod
    def init_app(app):
        """Initialize application"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.THUMBNAIL_FOLDER, exist_ok=True)
