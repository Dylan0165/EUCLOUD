import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, File, User, Folder, Activity
from datetime import datetime
import mimetypes
import zipfile
import io
from PIL import Image

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

def log_activity(user_id, activity_type, file_id=None, folder_id=None, details=None):
    """Helper function to log activities"""
    activity = Activity(
        user_id=user_id,
        file_id=file_id,
        folder_id=folder_id,
        activity_type=activity_type,
        activity_details=details
    )
    db.session.add(activity)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_thumbnail(file_path, thumbnail_path):
    """Generate thumbnail for image files"""
    try:
        img = Image.open(file_path)
        img.thumbnail((200, 200))
        img.save(thumbnail_path)
        return thumbnail_path
    except:
        return None

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check storage quota
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if user.storage_used + file_size > user.storage_quota:
            return jsonify({'error': 'Storage quota exceeded'}), 413
        
        # Get folder_id from form data
        folder_id = request.form.get('folder_id', type=int)
        
        # Verify folder ownership
        if folder_id:
            folder = Folder.query.get(folder_id)
            if not folder or folder.owner_id != user_id:
                return jsonify({'error': 'Invalid folder'}), 403
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get mime type
        mime_type = mimetypes.guess_type(filename)[0]
        
        # Generate thumbnail for images
        thumbnail_path = None
        if mime_type and mime_type.startswith('image/'):
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_full_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
            if generate_thumbnail(file_path, thumbnail_full_path):
                thumbnail_path = thumbnail_filename
        
        # Create database entry
        new_file = File(
            filename=filename,
            file_path=unique_filename,
            file_size=file_size,
            mime_type=mime_type,
            folder_id=folder_id,
            owner_id=user_id,
            thumbnail_path=thumbnail_path
        )
        
        db.session.add(new_file)
        
        # Update user storage
        user.storage_used += file_size
        
        # Log activity
        log_activity(user_id, 'upload', file_id=new_file.file_id, details=f'Uploaded {filename}')
        
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@files_bp.route('/list', methods=['GET'])
@jwt_required()
def list_files():
    """List files in a folder"""
    try:
        user_id = get_jwt_identity()
        folder_id = request.args.get('folder_id', type=int)
        
        # Build query
        query = File.query.filter_by(owner_id=user_id, is_deleted=False)
        
        if folder_id:
            query = query.filter_by(folder_id=folder_id)
        else:
            query = query.filter_by(folder_id=None)
        
        files = query.all()
        
        # Also get folders
        folder_query = Folder.query.filter_by(owner_id=user_id)
        if folder_id:
            folder_query = folder_query.filter_by(parent_folder_id=folder_id)
        else:
            folder_query = folder_query.filter_by(parent_folder_id=None)
        
        folders = folder_query.all()
        
        return jsonify({
            'files': [f.to_dict() for f in files],
            'folders': [f.to_dict() for f in folders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    """Get file details"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({'file': file.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download a file"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=file.filename)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/rename', methods=['PUT'])
@jwt_required()
def rename_file(file_id):
    """Rename a file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('filename'):
            return jsonify({'error': 'Filename is required'}), 400
        
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        file.filename = data['filename']
        file.modified_at = datetime.utcnow()
        
        # Log activity
        log_activity(user_id, 'rename', file_id=file_id, details=f'Renamed to {data["filename"]}')
        
        db.session.commit()
        
        return jsonify({
            'message': 'File renamed successfully',
            'file': file.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        # Mark as deleted (soft delete)
        file.is_deleted = True
        file.deleted_at = datetime.utcnow()
        
        # Update user storage
        user = User.query.get(user_id)
        user.storage_used -= file.file_size
        
        # Log activity
        log_activity(user_id, 'delete', file_id=file_id, details=f'Deleted {file.filename}')
        
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/move', methods=['POST'])
@jwt_required()
def move_file(file_id):
    """Move file to another folder"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        new_folder_id = data.get('folder_id')
        
        if new_folder_id:
            folder = Folder.query.get(new_folder_id)
            if not folder or folder.owner_id != user_id:
                return jsonify({'error': 'Invalid folder'}), 403
        
        file.folder_id = new_folder_id
        file.modified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'File moved successfully',
            'file': file.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/copy', methods=['POST'])
@jwt_required()
def copy_file(file_id):
    """Copy a file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        user = User.query.get(user_id)
        
        # Check storage quota
        if user.storage_used + file.file_size > user.storage_quota:
            return jsonify({'error': 'Storage quota exceeded'}), 413
        
        # Copy physical file
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
        new_filename = f"{uuid.uuid4()}_{file.filename}"
        new_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
        
        import shutil
        shutil.copy2(old_path, new_path)
        
        # Create new database entry
        new_file = File(
            filename=f"Copy of {file.filename}",
            file_path=new_filename,
            file_size=file.file_size,
            mime_type=file.mime_type,
            folder_id=data.get('folder_id', file.folder_id),
            owner_id=user_id,
            thumbnail_path=file.thumbnail_path
        )
        
        db.session.add(new_file)
        
        # Update user storage
        user.storage_used += file.file_size
        
        db.session.commit()
        
        return jsonify({
            'message': 'File copied successfully',
            'file': new_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/preview', methods=['GET'])
@jwt_required()
def preview_file(file_id):
    """Preview a file (for images, PDFs, text files)"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Return file with inline disposition for preview
        return send_file(file_path, mimetype=file.mime_type)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
