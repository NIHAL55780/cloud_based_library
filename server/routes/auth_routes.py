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


@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """Handle user registration via AWS Cognito"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        logger.info(f'Received signup data: {data}')
        
        if not data or 'email' not in data or 'password' not in data or 'username' not in data:
            logger.error('Missing required fields')
            return jsonify({
                'success': False,
                'error': 'Missing required fields: email, username, and password are required'
            }), 400
        
        email = data['email'].strip()
        password = data['password']
        username = data['username'].strip()
        
        logger.info(f'Signup attempt for user: {username}, email: {email}')
        
        # Sign up with Cognito - use EMAIL as username
        try:
            response = cognito_client.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,  # Use email as username
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'preferred_username', 'Value': username}
                ]
            )
            
            logger.info(f'User {username} signed up successfully with UserSub: {response["UserSub"]}')
            
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
            error_message = e.response['Error']['Message']
            
            # LOG THE FULL ERROR MESSAGE
            logger.error(f'Cognito ClientError: {error_code} - {error_message}')
            logger.error(f'Full error response: {e.response}')
            
            if error_code == 'UsernameExistsException':
                return jsonify({
                    'success': False,
                    'error': 'An account with this email already exists'
                }), 409
            elif error_code == 'InvalidPasswordException':
                return jsonify({
                    'success': False,
                    'error': f'Password does not meet requirements: {error_message}'
                }), 400
            elif error_code == 'InvalidParameterException':
                return jsonify({
                    'success': False,
                    'error': f'Invalid input: {error_message}',
                    'details': error_message
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'Registration failed',
                    'message': error_message,
                    'code': error_code
                }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error during signup: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


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
                'error': 'User account not confirmed. Please check your email.'
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


@auth_bp.route('/confirm', methods=['POST', 'OPTIONS'])
def confirm_signup():
    """Confirm user signup with verification code"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing email or verification code'
            }), 400
        
        email = data['email'].strip()
        code = data['code'].strip()
        
        logger.info(f'Confirming signup for email: {email}')
        
        try:
            # Confirm signup with Cognito
            response = cognito_client.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,  # Use email as username (same as signup)
                ConfirmationCode=code
            )
            
            logger.info(f'User {email} confirmed successfully')
            
            return jsonify({
                'success': True,
                'message': 'Email verified successfully. You can now log in.'
            }), 200
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f'Cognito error during confirmation: {error_code} - {error_message}')
            
            if error_code == 'CodeMismatchException':
                return jsonify({
                    'success': False,
                    'error': 'Invalid verification code'
                }), 400
            elif error_code == 'ExpiredCodeException':
                return jsonify({
                    'success': False,
                    'error': 'Verification code has expired'
                }), 400
            elif error_code == 'NotAuthorizedException':
                return jsonify({
                    'success': False,
                    'error': 'User is already confirmed'
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'Verification failed',
                    'message': error_message
                }), 500
                
    except Exception as e:
        logger.error(f'Unexpected error during confirmation: {str(e)}')
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
