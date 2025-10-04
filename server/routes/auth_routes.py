"""
Authentication routes for Cloud-Based Digital Library Backend
Handles user signup and login using AWS Cognito
"""

import boto3
from flask import Blueprint, request, jsonify
from botocore.exceptions import ClientError
import re

from config import Config

# Create Blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=Config.AWS_REGION)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    User signup endpoint
    POST /auth/signup
    Body: {"email": "user@example.com", "password": "SecurePass123"}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide email and password in JSON format'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate input
        if not email or not password:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Both email and password are required'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Validate password strength
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({
                'error': 'Weak password',
                'message': password_message
            }), 400
        
        # Attempt to sign up user with Cognito
        try:
            response = cognito_client.sign_up(
                ClientId=Config.COGNITO_CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    }
                ]
            )
            
            return jsonify({
                'message': 'User created successfully',
                'user_sub': response['UserSub'],
                'confirmation_required': response.get('CodeDeliveryDetails', {}).get('Destination', ''),
                'next_step': 'Please check your email for verification code'
            }), 201
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'UsernameExistsException':
                return jsonify({
                    'error': 'User already exists',
                    'message': 'An account with this email already exists'
                }), 409
            elif error_code == 'InvalidPasswordException':
                return jsonify({
                    'error': 'Invalid password',
                    'message': 'Password does not meet requirements'
                }), 400
            elif error_code == 'InvalidParameterException':
                return jsonify({
                    'error': 'Invalid parameters',
                    'message': 'Please check your input and try again'
                }), 400
            else:
                return jsonify({
                    'error': 'Signup failed',
                    'message': f'AWS Error: {error_message}'
                }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during signup'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    POST /auth/login
    Body: {"email": "user@example.com", "password": "SecurePass123"}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide email and password in JSON format'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate input
        if not email or not password:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Both email and password are required'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Attempt to authenticate user with Cognito
        try:
            response = cognito_client.initiate_auth(
                ClientId=Config.COGNITO_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            # Extract tokens from response
            auth_result = response['AuthenticationResult']
            
            return jsonify({
                'message': 'Login successful',
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn']
            }), 200
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Invalid email or password'
                }), 401
            elif error_code == 'UserNotConfirmedException':
                return jsonify({
                    'error': 'User not confirmed',
                    'message': 'Please verify your email address before logging in'
                }), 401
            elif error_code == 'UserNotFoundException':
                return jsonify({
                    'error': 'User not found',
                    'message': 'No account found with this email address'
                }), 404
            elif error_code == 'TooManyRequestsException':
                return jsonify({
                    'error': 'Too many requests',
                    'message': 'Please wait before trying again'
                }), 429
            else:
                return jsonify({
                    'error': 'Login failed',
                    'message': f'AWS Error: {error_message}'
                }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during login'
        }), 500

@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """Health check endpoint for auth service"""
    return jsonify({
        'status': 'healthy',
        'service': 'authentication',
        'message': 'Auth service is running'
    }), 200
