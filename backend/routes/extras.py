from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, File, Tag, FileTag, Comment, Activity
from datetime import datetime

extras_bp = Blueprint('extras', __name__, url_prefix='/api')

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

# FAVORITES
@extras_bp.route('/favorites/toggle/<int:file_id>', methods=['POST'])
@jwt_required()
def toggle_favorite(file_id):
    """Toggle favorite status"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        file.is_favorite = not file.is_favorite
        
        log_activity(
            user_id, 
            'favorite' if file.is_favorite else 'unfavorite',
            file_id=file_id,
            details=f'{"Favorited" if file.is_favorite else "Unfavorited"} {file.filename}'
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Favorite toggled',
            'is_favorite': file.is_favorite
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/favorites/list', methods=['GET'])
@jwt_required()
def list_favorites():
    """List favorite files"""
    try:
        user_id = get_jwt_identity()
        favorites = File.query.filter_by(
            owner_id=user_id,
            is_favorite=True,
            is_deleted=False
        ).all()
        
        return jsonify({
            'files': [f.to_dict() for f in favorites]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# TAGS
@extras_bp.route('/tags/create', methods=['POST'])
@jwt_required()
def create_tag():
    """Create a new tag"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('tag_name'):
            return jsonify({'error': 'Tag name is required'}), 400
        
        tag = Tag(
            tag_name=data['tag_name'],
            color=data.get('color', '#667eea'),
            user_id=user_id
        )
        
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'message': 'Tag created',
            'tag': tag.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/tags/list', methods=['GET'])
@jwt_required()
def list_tags():
    """List all tags"""
    try:
        user_id = get_jwt_identity()
        tags = Tag.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'tags': [t.to_dict() for t in tags]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/tags/add-to-file/<int:file_id>', methods=['POST'])
@jwt_required()
def add_tag_to_file(file_id):
    """Add tag to file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        file = File.query.get(file_id)
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        tag_id = data.get('tag_id')
        tag = Tag.query.get(tag_id)
        
        if not tag or tag.user_id != user_id:
            return jsonify({'error': 'Tag not found'}), 404
        
        # Check if already tagged
        existing = FileTag.query.filter_by(file_id=file_id, tag_id=tag_id).first()
        if existing:
            return jsonify({'error': 'File already has this tag'}), 400
        
        file_tag = FileTag(file_id=file_id, tag_id=tag_id)
        db.session.add(file_tag)
        
        log_activity(user_id, 'tag', file_id=file_id, details=f'Tagged {file.filename} with {tag.tag_name}')
        
        db.session.commit()
        
        return jsonify({'message': 'Tag added to file'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/tags/file/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_tags(file_id):
    """Get tags for a file"""
    try:
        user_id = get_jwt_identity()
        file = File.query.get(file_id)
        
        if not file or file.owner_id != user_id:
            return jsonify({'error': 'File not found'}), 404
        
        file_tags = db.session.query(Tag).join(FileTag).filter(
            FileTag.file_id == file_id
        ).all()
        
        return jsonify({
            'tags': [t.to_dict() for t in file_tags]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# COMMENTS
@extras_bp.route('/comments/add/<int:file_id>', methods=['POST'])
@jwt_required()
def add_comment(file_id):
    """Add comment to file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        file = File.query.get(file_id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        comment = Comment(
            file_id=file_id,
            user_id=user_id,
            comment_text=data.get('comment_text'),
            parent_comment_id=data.get('parent_comment_id')
        )
        
        db.session.add(comment)
        
        log_activity(user_id, 'comment', file_id=file_id, details=f'Commented on {file.filename}')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/comments/file/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_comments(file_id):
    """Get comments for a file"""
    try:
        comments = Comment.query.filter_by(file_id=file_id).order_by(Comment.created_at.desc()).all()
        
        return jsonify({
            'comments': [c.to_dict() for c in comments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@extras_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment"""
    try:
        user_id = get_jwt_identity()
        comment = Comment.query.get(comment_id)
        
        if not comment or comment.user_id != user_id:
            return jsonify({'error': 'Comment not found'}), 404
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': 'Comment deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ACTIVITIES
@extras_bp.route('/activities/list', methods=['GET'])
@jwt_required()
def list_activities():
    """List recent activities"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        activities = Activity.query.filter_by(user_id=user_id).order_by(
            Activity.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'activities': [a.to_dict() for a in activities]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
