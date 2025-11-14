from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Folder, File
from datetime import datetime

folders_bp = Blueprint('folders', __name__, url_prefix='/api/folders')

@folders_bp.route('/create', methods=['POST'])
@jwt_required()
def create_folder():
    """Create a new folder"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('folder_name'):
            return jsonify({'error': 'Folder name is required'}), 400
        
        parent_folder_id = data.get('parent_folder_id')
        
        # Verify parent folder ownership if specified
        if parent_folder_id:
            parent = Folder.query.get(parent_folder_id)
            if not parent or parent.owner_id != user_id:
                return jsonify({'error': 'Invalid parent folder'}), 403
        
        # Create folder
        folder = Folder(
            folder_name=data['folder_name'],
            parent_folder_id=parent_folder_id,
            owner_id=user_id
        )
        
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'message': 'Folder created successfully',
            'folder': folder.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/list', methods=['GET'])
@jwt_required()
def list_folders():
    """List all folders"""
    try:
        user_id = get_jwt_identity()
        folders = Folder.query.filter_by(owner_id=user_id).all()
        
        return jsonify({
            'folders': [f.to_dict() for f in folders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>', methods=['GET'])
@jwt_required()
def get_folder(folder_id):
    """Get folder details"""
    try:
        user_id = get_jwt_identity()
        folder = Folder.query.get(folder_id)
        
        if not folder or folder.owner_id != user_id:
            return jsonify({'error': 'Folder not found'}), 404
        
        return jsonify({
            'folder': folder.to_dict(include_children=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>/rename', methods=['PUT'])
@jwt_required()
def rename_folder(folder_id):
    """Rename a folder"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('folder_name'):
            return jsonify({'error': 'Folder name is required'}), 400
        
        folder = Folder.query.get(folder_id)
        
        if not folder or folder.owner_id != user_id:
            return jsonify({'error': 'Folder not found'}), 404
        
        folder.folder_name = data['folder_name']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Folder renamed successfully',
            'folder': folder.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def delete_folder(folder_id):
    """Delete a folder"""
    try:
        user_id = get_jwt_identity()
        folder = Folder.query.get(folder_id)
        
        if not folder or folder.owner_id != user_id:
            return jsonify({'error': 'Folder not found'}), 404
        
        # Check if folder is empty
        has_files = File.query.filter_by(folder_id=folder_id, is_deleted=False).first()
        has_subfolders = Folder.query.filter_by(parent_folder_id=folder_id).first()
        
        if has_files or has_subfolders:
            return jsonify({'error': 'Folder is not empty'}), 400
        
        db.session.delete(folder)
        db.session.commit()
        
        return jsonify({'message': 'Folder deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
