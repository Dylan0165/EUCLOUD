import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Share, File, User
from datetime import datetime, timedelta

shares_bp = Blueprint('shares', __name__, url_prefix='/api/share')

@shares_bp.route('/create', methods=['POST'])
@jwt_required()
def create_share():
    """Create a share link for a file"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.get_json()
        
        if not data or not data.get('file_id'):
            return jsonify({'error': 'File ID is required'}), 400
        
        file = File.query.get(data['file_id'])
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        # Generate unique share ID
        share_id = str(uuid.uuid4())[:12]
        
        # Calculate expiration
        expires_at = None
        if data.get('expires_in_days'):
            expires_at = datetime.utcnow() + timedelta(days=data['expires_in_days'])
        
        # Create share
        share = Share(
            share_id=share_id,
            file_id=file.file_id,
            created_by=user_id,
            access_type=data.get('access_type', 'view'),
            expires_at=expires_at
        )
        
        # Set password if provided
        if data.get('password'):
            share.set_password(data['password'])
        
        db.session.add(share)
        db.session.commit()
        
        return jsonify({
            'message': 'Share created successfully',
            'share': share.to_dict(),
            'share_url': f'/share/{share_id}'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@shares_bp.route('/<share_id>', methods=['GET'])
def get_share(share_id):
    """Get share details and file (public endpoint)"""
    try:
        share = Share.query.get(share_id)
        
        if not share:
            return jsonify({'error': 'Share not found'}), 404
        
        if share.is_expired():
            return jsonify({'error': 'Share has expired'}), 410
        
        # Check password
        password = request.args.get('password')
        if share.password_hash and not share.check_password(password):
            return jsonify({
                'error': 'Password required',
                'requires_password': True
            }), 401
        
        file = File.query.get(share.file_id)
        
        return jsonify({
            'share': share.to_dict(),
            'file': file.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shares_bp.route('/<share_id>', methods=['DELETE'])
@jwt_required()
def delete_share(share_id):
    """Delete a share"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        share = Share.query.get(share_id)
        
        if not share or share.created_by != user_id:
            return jsonify({'error': 'Share not found'}), 404
        
        db.session.delete(share)
        db.session.commit()
        
        return jsonify({'message': 'Share deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
