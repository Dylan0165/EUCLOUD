from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, File, User, Activity
from datetime import datetime, timedelta

trash_bp = Blueprint('trash', __name__, url_prefix='/api/trash')

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

@trash_bp.route('/list', methods=['GET'])
@jwt_required()
def list_trash():
    """List deleted files"""
    try:
        user_id = get_jwt_identity()
        deleted_files = File.query.filter_by(
            owner_id=user_id,
            is_deleted=True
        ).order_by(File.deleted_at.desc()).all()
        
        return jsonify({
            'files': [f.to_dict() for f in deleted_files]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trash_bp.route('/restore/<int:file_id>', methods=['POST'])
@jwt_required()
def restore_file(file_id):
    """Restore file from trash"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        if not file.is_deleted:
            return jsonify({'error': 'File is not in trash'}), 400
        
        # Restore file
        file.is_deleted = False
        file.deleted_at = None
        
        # Update user storage
        user = User.query.get(user_id)
        user.storage_used += file.file_size
        
        # Log activity
        log_activity(user_id, 'restore', file_id=file_id, details=f'Restored {file.filename}')
        
        db.session.commit()
        
        return jsonify({
            'message': 'File restored successfully',
            'file': file.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trash_bp.route('/permanent-delete/<int:file_id>', methods=['DELETE'])
@jwt_required()
def permanent_delete(file_id):
    """Permanently delete file"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        import os
        from flask import current_app
        
        # Delete physical file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail
        if file.thumbnail_path:
            thumb_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], file.thumbnail_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
        # Log activity
        log_activity(user_id, 'permanent_delete', file_id=file_id, details=f'Permanently deleted {file.filename}')
        
        # Delete from database
        db.session.delete(file)
        db.session.commit()
        
        return jsonify({'message': 'File permanently deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trash_bp.route('/empty', methods=['POST'])
@jwt_required()
def empty_trash():
    """Empty entire trash"""
    try:
        user_id = get_jwt_identity()
        deleted_files = File.query.filter_by(owner_id=user_id, is_deleted=True).all()
        
        import os
        from flask import current_app
        
        for file in deleted_files:
            # Delete physical file
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete thumbnail
            if file.thumbnail_path:
                thumb_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], file.thumbnail_path)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            
            db.session.delete(file)
        
        # Log activity
        log_activity(user_id, 'empty_trash', details=f'Emptied trash ({len(deleted_files)} files)')
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(deleted_files)} files permanently deleted'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trash_bp.route('/auto-delete', methods=['POST'])
@jwt_required()
def auto_delete_old():
    """Auto-delete files older than 30 days in trash"""
    try:
        user_id = get_jwt_identity()
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        old_files = File.query.filter(
            File.owner_id == user_id,
            File.is_deleted == True,
            File.deleted_at < thirty_days_ago
        ).all()
        
        import os
        from flask import current_app
        
        for file in old_files:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if file.thumbnail_path:
                thumb_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], file.thumbnail_path)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            
            db.session.delete(file)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(old_files)} old files auto-deleted'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
