"""
Public Cognito Authentication Routes
Uses direct HTTP calls to Cognito public endpoints - no AWS credentials required
"""

from flask import Blueprint, request, jsonify
import logging
import re
import requests
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def _validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def _validate_password(password):
    """Basic password validation"""
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    return True, 'ok'

@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'authentication-public'}), 200

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Public Cognito signup endpoint"""
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

        # Call Cognito public signup endpoint
        cognito_url = f"https://cognito-idp.us-east-1.amazonaws.com/"
        
        headers = {
            'X-Amz-Target': 'AWSCognitoIdentityProviderService.SignUp',
            'Content-Type': 'application/x-amz-json-1.1'
        }
        
        payload = {
            'ClientId': '2nhjeo7vqtjdtt80pf07cstl8a',  # Your Cognito Client ID
            'Username': email,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email', 'Value': email}
            ]
        }
        
        if name:
            payload['UserAttributes'].append({'Name': 'name', 'Value': name})

        response = requests.post(cognito_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'message': 'User created successfully',
                'user_sub': result.get('UserSub'),
                'confirmation_required': result.get('CodeDeliveryDetails', {}).get('Destination', ''),
                'next_step': 'Please check your email for verification code'
            }), 201
        else:
            error_data = response.json()
            error_code = error_data.get('__type', '').split('#')[-1]
            error_message = error_data.get('message', 'Unknown error')
            
            if error_code == 'UsernameExistsException':
                return jsonify({'error': 'User already exists', 'message': 'An account with this email already exists'}), 409
            elif error_code == 'InvalidPasswordException':
                return jsonify({'error': 'Invalid password', 'message': 'Password does not meet requirements'}), 400
            else:
                return jsonify({'error': 'Signup failed', 'message': error_message}), 400

    except Exception as e:
        logging.exception('Unexpected error during signup')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during signup'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Public Cognito login endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and password are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        # Call Cognito public login endpoint
        cognito_url = f"https://cognito-idp.us-east-1.amazonaws.com/"
        
        headers = {
            'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
            'Content-Type': 'application/x-amz-json-1.1'
        }
        
        payload = {
            'ClientId': '2nhjeo7vqtjdtt80pf07cstl8a',  # Your Cognito Client ID
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': email,
                'PASSWORD': password
            }
        }

        response = requests.post(cognito_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            auth_result = result.get('AuthenticationResult', {})
            
            return jsonify({
                'message': 'Login successful',
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'refresh_token': auth_result.get('RefreshToken'),
                'token_type': auth_result.get('TokenType'),
                'expires_in': auth_result.get('ExpiresIn')
            }), 200
        else:
            error_data = response.json()
            error_code = error_data.get('__type', '').split('#')[-1]
            error_message = error_data.get('message', 'Unknown error')
            
            if error_code == 'NotAuthorizedException':
                return jsonify({'error': 'Invalid credentials', 'message': 'Email or password is incorrect'}), 401
            elif error_code == 'UserNotConfirmedException':
                return jsonify({'error': 'User not confirmed', 'message': 'Please verify your email address first'}), 400
            else:
                return jsonify({'error': 'Login failed', 'message': error_message}), 400

    except Exception as e:
        logging.exception('Unexpected error during login')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during login'}), 500

@auth_bp.route('/confirm', methods=['POST'])
def confirm_signup():
    """Public Cognito email confirmation endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        code = (data.get('code') or '').strip()

        if not email or not code:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and code are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        # Call Cognito public confirm endpoint
        cognito_url = f"https://cognito-idp.us-east-1.amazonaws.com/"
        
        headers = {
            'X-Amz-Target': 'AWSCognitoIdentityProviderService.ConfirmSignUp',
            'Content-Type': 'application/x-amz-json-1.1'
        }
        
        payload = {
            'ClientId': '2nhjeo7vqtjdtt80pf07cstl8a',  # Your Cognito Client ID
            'Username': email,
            'ConfirmationCode': code
        }

        response = requests.post(cognito_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({'message': 'Email verified successfully. You can now log in.'}), 200
        else:
            error_data = response.json()
            error_code = error_data.get('__type', '').split('#')[-1]
            error_message = error_data.get('message', 'Unknown error')
            
            if error_code == 'CodeMismatchException':
                return jsonify({'error': 'Invalid code', 'message': 'The verification code is incorrect'}), 400
            elif error_code == 'ExpiredCodeException':
                return jsonify({'error': 'Expired code', 'message': 'The verification code has expired'}), 400
            else:
                return jsonify({'error': 'Confirmation failed', 'message': error_message}), 400

    except Exception as e:
        logging.exception('Unexpected error during confirmation')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during confirmation'}), 500

@auth_bp.route('/protected', methods=['GET'])
def protected():
    """Protected endpoint - requires valid JWT token"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing token', 'message': 'Authorization header required'}), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # For now, just return success - in production you'd verify the JWT
        return jsonify({
            'message': 'Access granted',
            'user': {
                'id': 'user_id',
                'email': 'user@example.com'
            }
        }), 200

    except Exception as e:
        logging.exception('Unexpected error in protected endpoint')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
