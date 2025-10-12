"""
Mock Authentication Routes for Development
Simple in-memory authentication without AWS Cognito
"""

from flask import Blueprint, request, jsonify
import logging
import uuid
from datetime import datetime, timedelta
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# In-memory storage for development (replace with database in production)
users_db = {}
sessions_db = {}

def _validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def _validate_password(password):
    """Basic password validation"""
    if len(password) < 6:
        return False, 'Password must be at least 6 characters long'
    return True, 'ok'

def _generate_token(user_id):
    """Generate a simple token for development"""
    token = str(uuid.uuid4())
    sessions_db[token] = {
        'user_id': user_id,
        'created_at': datetime.now(),
        'expires_at': datetime.now() + timedelta(hours=24)
    }
    return token

@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'authentication-mock'}), 200

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Mock signup endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        name = (data.get('name') or '').strip()

        if not email or not password:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and password are required'}), 400
        
        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400
        
        ok, msg = _validate_password(password)
        if not ok:
            return jsonify({'error': 'Weak password', 'message': msg}), 400

        # Check if user already exists
        if email in users_db:
            return jsonify({'error': 'User already exists', 'message': 'An account with this email already exists'}), 409

        # Create new user
        user_id = str(uuid.uuid4())
        users_db[email] = {
            'id': user_id,
            'email': email,
            'name': name or email.split('@')[0],
            'password': password,  # In production, hash this!
            'created_at': datetime.now().isoformat(),
            'verified': True  # Mock: auto-verify for development
        }

        logging.info(f'Mock user created: {email}')

        return jsonify({
            'message': 'User created successfully',
            'user_sub': user_id,
            'confirmation_required': False,
            'next_step': 'You can now log in'
        }), 201

    except Exception as e:
        logging.exception('Unexpected error during mock signup')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during signup'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Mock login endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and password are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        # Check if user exists and password matches
        if email not in users_db:
            return jsonify({'error': 'Invalid credentials', 'message': 'Email or password is incorrect'}), 401

        user = users_db[email]
        if user['password'] != password:  # In production, use proper password hashing!
            return jsonify({'error': 'Invalid credentials', 'message': 'Email or password is incorrect'}), 401

        # Generate tokens
        access_token = _generate_token(user['id'])
        id_token = _generate_token(user['id'])

        logging.info(f'Mock user logged in: {email}')

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'id_token': id_token,
            'refresh_token': access_token,  # Mock: same as access token
            'token_type': 'Bearer',
            'expires_in': 86400  # 24 hours
        }), 200

    except Exception as e:
        logging.exception('Unexpected error during mock login')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during login'}), 500

@auth_bp.route('/confirm', methods=['POST'])
def confirm_signup():
    """Mock email confirmation endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        code = (data.get('code') or '').strip()

        if not email or not code:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and code are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        # Mock: accept any code for development
        if email in users_db:
            users_db[email]['verified'] = True
            return jsonify({'message': 'Email verified successfully. You can now log in.'}), 200
        else:
            return jsonify({'error': 'User not found', 'message': 'No account found with this email address'}), 404

    except Exception as e:
        logging.exception('Unexpected error during mock confirmation')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during confirmation'}), 500

@auth_bp.route('/protected', methods=['GET'])
def protected():
    """Mock protected endpoint"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing token', 'message': 'Authorization header required'}), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Check if token is valid
        if token not in sessions_db:
            return jsonify({'error': 'Invalid token', 'message': 'Token not found or expired'}), 401

        session = sessions_db[token]
        if datetime.now() > session['expires_at']:
            del sessions_db[token]
            return jsonify({'error': 'Token expired', 'message': 'Please log in again'}), 401

        # Find user by ID
        user_id = session['user_id']
        user = None
        for email, user_data in users_db.items():
            if user_data['id'] == user_id:
                user = user_data
                break

        if not user:
            return jsonify({'error': 'User not found', 'message': 'User associated with token not found'}), 401

        return jsonify({
            'message': 'Access granted',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name']
            }
        }), 200

    except Exception as e:
        logging.exception('Unexpected error in mock protected endpoint')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
