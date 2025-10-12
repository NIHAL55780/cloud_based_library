from flask import Blueprint, request, jsonify
import logging
import re
import time
import requests
from jose import jwt, jwk
from jose.utils import base64url_decode
import boto3
from botocore.exceptions import ClientError, ParamValidationError

from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize boto3 Cognito client (only if AWS credentials are available)
try:
    cognito_client = boto3.client('cognito-idp', region_name=Config.AWS_REGION)
except Exception as e:
    logging.warning(f"Cognito client initialization failed: {e}")
    cognito_client = None

# JWKS caching
_JWKS_CACHE = {
    'keys': None,
    'fetched_at': 0,
    'ttl_seconds': 3600
}

def _get_jwks():
    """Fetch and cache JWKS from Cognito."""
    now = time.time()
    if _JWKS_CACHE['keys'] and (now - _JWKS_CACHE['fetched_at'] < _JWKS_CACHE['ttl_seconds']):
        return _JWKS_CACHE['keys']
    jwks_url = f"https://cognito-idp.{Config.AWS_REGION}.amazonaws.com/{Config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    try:
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        _JWKS_CACHE['keys'] = data.get('keys', [])
        _JWKS_CACHE['fetched_at'] = now
        return _JWKS_CACHE['keys']
    except Exception as exc:
        logging.error("Failed to fetch JWKS: %s", exc)
        return []

def verify_jwt(token: str):
    """Verify Cognito JWT token and return claims if valid."""
    headers = jwt.get_unverified_headers(token)
    kid = headers.get('kid')
    if not kid:
        raise ValueError('Missing kid in token header')

    keys = _get_jwks()
    key = next((k for k in keys if k.get('kid') == kid), None)
    if not key:
        raise ValueError('Signing key not found')

    # jose can take the jwk dict directly
    claims = jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience=Config.COGNITO_CLIENT_ID,
        options={
            'verify_aud': True,
            'verify_at_hash': False
        }
    )
    return claims

def _validate_email(email: str) -> bool:
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email or '') is not None

def _validate_password(password: str):
    if not password or len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    return True, 'ok'

def _ensure_config():
    if not Config.COGNITO_CLIENT_ID or not Config.COGNITO_USER_POOL_ID:
        raise RuntimeError('Server misconfiguration: missing Cognito env vars')
    if not cognito_client:
        raise RuntimeError('Cognito client not available: check AWS credentials')

# Health check
@auth_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'authentication'}), 200

# Signup route
@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        _ensure_config()
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and password are required'}), 400
        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400
        ok, msg = _validate_password(password)
        if not ok:
            return jsonify({'error': 'Weak password', 'message': msg}), 400

        try:
            response = cognito_client.sign_up(
                ClientId=Config.COGNITO_CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[{'Name': 'email', 'Value': email}]
            )
            return jsonify({
                'message': 'User created successfully',
                'user_sub': response.get('UserSub'),
                'confirmation_required': response.get('CodeDeliveryDetails', {}).get('Destination', ''),
                'next_step': 'Please check your email for verification code'
            }), 201
        except ClientError as ce:
            code = ce.response['Error'].get('Code')
            if code == 'UsernameExistsException':
                return jsonify({'error': 'User already exists', 'message': 'An account with this email already exists'}), 409
            if code == 'InvalidPasswordException':
                return jsonify({'error': 'Invalid password', 'message': 'Password does not meet requirements'}), 400
            if code == 'InvalidParameterException':
                return jsonify({'error': 'Invalid parameters', 'message': 'Please check your input and try again'}), 400
            logging.exception('Signup failed')
            return jsonify({'error': 'Signup failed', 'message': ce.response['Error'].get('Message', 'AWS error')}), 500
        except ParamValidationError as pve:
            return jsonify({'error': 'Server misconfiguration', 'message': str(pve)}), 500
    except RuntimeError as re_err:
        return jsonify({'error': 'Server misconfiguration', 'message': str(re_err)}), 500
    except Exception:
        logging.exception('Unexpected error during signup')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during signup'}), 500

# Login route
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        _ensure_config()
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and password are required'}), 400
        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        try:
            response = cognito_client.initiate_auth(
                ClientId=Config.COGNITO_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={'USERNAME': email, 'PASSWORD': password}
            )
            result = response.get('AuthenticationResult', {})
            return jsonify({
                'message': 'Login successful',
                'access_token': result.get('AccessToken'),
                'id_token': result.get('IdToken'),
                'refresh_token': result.get('RefreshToken'),
                'token_type': result.get('TokenType'),
                'expires_in': result.get('ExpiresIn')
            }), 200
        except ClientError as ce:
            code = ce.response['Error'].get('Code')
            if code == 'NotAuthorizedException':
                return jsonify({'error': 'Authentication failed', 'message': 'Invalid email or password'}), 401
            if code == 'UserNotConfirmedException':
                return jsonify({'error': 'User not confirmed', 'message': 'Please verify your email address before logging in'}), 401
            if code == 'UserNotFoundException':
                return jsonify({'error': 'User not found', 'message': 'No account found with this email address'}), 404
            if code == 'TooManyRequestsException':
                return jsonify({'error': 'Too many requests', 'message': 'Please wait before trying again'}), 429
            logging.exception('Login failed')
            return jsonify({'error': 'Login failed', 'message': ce.response['Error'].get('Message', 'AWS error')}), 500
        except ParamValidationError as pve:
            return jsonify({'error': 'Server misconfiguration', 'message': str(pve)}), 500
    except RuntimeError as re_err:
        return jsonify({'error': 'Server misconfiguration', 'message': str(re_err)}), 500
    except Exception:
        logging.exception('Unexpected error during login')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during login'}), 500

# Protected route example
@auth_bp.route('/protected', methods=['GET'])
def protected():
    auth_header = request.headers.get('Authorization')
    if not auth_header or ' ' not in auth_header:
        return jsonify({'error': 'Missing token'}), 401
    token = auth_header.split(' ', 1)[1]
    try:
        claims = verify_jwt(token)
        return jsonify({'message': 'Authorized', 'user': claims.get('username') or claims.get('cognito:username')}), 200
    except Exception as e:
        return jsonify({'error': 'Unauthorized', 'details': str(e)}), 401

# Confirm signup route
@auth_bp.route('/confirm', methods=['POST'])
def confirm_signup():
    try:
        _ensure_config()
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        code = (data.get('code') or '').strip()

        if not email or not code:
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and code are required'}), 400
        if not _validate_email(email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        try:
            cognito_client.confirm_sign_up(
                ClientId=Config.COGNITO_CLIENT_ID,
                Username=email,
                ConfirmationCode=code,
                ForceAliasCreation=False
            )
            return jsonify({'message': 'Email verified successfully. You can now log in.'}), 200
        except ClientError as ce:
            code_name = ce.response['Error'].get('Code')
            if code_name == 'CodeMismatchException':
                return jsonify({'error': 'Invalid code', 'message': 'The verification code is incorrect'}), 400
            if code_name == 'ExpiredCodeException':
                return jsonify({'error': 'Expired code', 'message': 'The verification code has expired'}), 400
            if code_name == 'UserNotFoundException':
                return jsonify({'error': 'User not found', 'message': 'No account found with this email address'}), 404
            if code_name == 'NotAuthorizedException':
                return jsonify({'error': 'Already confirmed', 'message': 'This user is already confirmed'}), 400
            logging.exception('Confirm signup failed')
            return jsonify({'error': 'Confirmation failed', 'message': ce.response['Error'].get('Message', 'AWS error')}), 500
        except ParamValidationError as pve:
            return jsonify({'error': 'Server misconfiguration', 'message': str(pve)}), 500
    except RuntimeError as re_err:
        return jsonify({'error': 'Server misconfiguration', 'message': str(re_err)}), 500
    except Exception:
        logging.exception('Unexpected error during confirmation')
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred during confirmation'}), 500
