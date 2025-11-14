from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
import os

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    JWTManager(app)
    
    # Initialize config
    config_class.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.files import files_bp
    from routes.folders import folders_bp
    from routes.shares import shares_bp
    from routes.storage import storage_bp
    from routes.trash import trash_bp
    from routes.extras import extras_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(shares_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(trash_bp)
    app.register_blueprint(extras_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        return {'message': 'EUCLOUD API is running', 'version': '1.0.0'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
