"""
Main Flask application for Cloud-Based Digital Library Backend
Handles CORS, route registration, and application initialization
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging

from config import Config
from routes.auth_routes import auth_bp
from routes.library_routes import library_bp

def create_app():
    """Application factory pattern for creating Flask app"""
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if Config.DEBUG else logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s - %(message)s'
    )
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)

    # Configure CORS (no credentials unless using cookies)
    CORS(
        app,
        origins=Config.CORS_ORIGINS,
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
        supports_credentials=False
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(library_bp)
    
    # Base route to confirm API is running
    @app.route('/')
    def index():
        """Base route to confirm API is running"""
        return jsonify({
            'message': 'Cloud-Based Digital Library API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'auth': {
                    'signup': 'POST /auth/signup',
                    'login': 'POST /auth/login',
                    'health': 'GET /auth/health',
                    'protected': 'GET /auth/protected'
                },
                'library': {
                    'get_all_books': 'GET /books',
                    'get_book_url': 'GET /book/<filename>',
                    'health_check': 'GET /health'
                }
            }
        }), 200
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'cloud-library-api',
            'version': '1.0.0'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'The requested endpoint does not exist'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method Not Allowed', 'message': 'The requested method is not allowed for this endpoint'}), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
