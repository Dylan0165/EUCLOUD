from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, File
from sqlalchemy import func

storage_bp = Blueprint('storage', __name__, url_prefix='/api/storage')

@storage_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_storage_usage():
    """Get current user storage usage"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'storage_used': user.storage_used,
            'storage_quota': user.storage_quota,
            'storage_available': user.storage_quota - user.storage_used,
            'usage_percentage': (user.storage_used / user.storage_quota * 100) if user.storage_quota > 0 else 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@storage_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_storage_stats():
    """Get detailed storage statistics"""
    try:
        user_id = get_jwt_identity()
        
        # Get file count by type
        stats = db.session.query(
            File.mime_type,
            func.count(File.file_id).label('count'),
            func.sum(File.file_size).label('total_size')
        ).filter_by(
            owner_id=user_id,
            is_deleted=False
        ).group_by(File.mime_type).all()
        
        # Format results
        file_types = []
        for mime_type, count, total_size in stats:
            file_types.append({
                'mime_type': mime_type or 'unknown',
                'count': count,
                'total_size': total_size or 0
            })
        
        # Get total file count
        total_files = File.query.filter_by(owner_id=user_id, is_deleted=False).count()
        
        return jsonify({
            'total_files': total_files,
            'file_types': file_types
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
