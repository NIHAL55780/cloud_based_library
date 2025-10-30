from flask import Blueprint, request, jsonify
import boto3
from botocore.exceptions import ClientError
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
COGNITO_USER_POOL_ID = 'us-east-1_IafPtJsIJ'
COGNITO_CLIENT_ID = '2nhjeo7vqtjdtt80pf07cstl8a'


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Handle user login via AWS Cognito"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing username or password'
            }), 400
        
        username = data['username']
        password = data['password']
        
        logger.info(f'Login attempt for user: {username}')
        
        # Authenticate with Cognito
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Get tokens
        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']
        
        logger.info(f'User {username} logged in successfully')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'tokens': {
                'idToken': id_token,
                'accessToken': access_token,
                'refreshToken': refresh_token
            },
            'user': {
                'username': username
            }
        }), 200
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f'Cognito error during login: {error_code}')
        
        if error_code == 'NotAuthorizedException':
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        elif error_code == 'UserNotFoundException':
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        elif error_code == 'UserNotConfirmedException':
            return jsonify({
                'success': False,
                'error': 'User account not confirmed'
            }), 403
        else:
            return jsonify({
                'success': False,
                'error': 'Authentication failed',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f'Unexpected error during login: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """Handle user registration via AWS Cognito"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data or 'username' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        email = data['email']
        password = data['password']
        username = data['username']
        
        logger.info(f'Signup attempt for user: {username}')
        
        # Sign up with Cognito
        response = cognito_client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        
        logger.info(f'User {username} signed up successfully')
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully. Please check your email to verify your account.',
            'user': {
                'username': username,
                'email': email,
                'userSub': response['UserSub']
            }
        }), 201
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f'Cognito error during signup: {error_code}')
        
        if error_code == 'UsernameExistsException':
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 409
        elif error_code == 'InvalidPasswordException':
            return jsonify({
                'success': False,
                'error': 'Password does not meet requirements'
            }), 400
        elif error_code == 'InvalidParameterException':
            return jsonify({
                'success': False,
                'error': 'Invalid input parameters'
            }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Registration failed',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f'Unexpected error during signup: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'auth'
    }), 200
