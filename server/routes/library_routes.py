"""
Library Routes for Cloud-Based Digital Library Backend
Handles book management and S3 operations
"""

from flask import Blueprint, request, jsonify
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from config import Config

# Initialize the blueprint
library_bp = Blueprint('library', __name__)

# Configure logging
logger = logging.getLogger(__name__)


def get_s3_client():
    """Initialize and return S3 client with credentials from environment"""
    try:
        if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
            raise NoCredentialsError("AWS credentials not configured")
        
        # Build client parameters
        client_params = {
            'aws_access_key_id': Config.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': Config.AWS_SECRET_ACCESS_KEY,
            'region_name': Config.AWS_REGION
        }
        
        # Add session token if available (for temporary credentials)
        if Config.AWS_SESSION_TOKEN:
            client_params['aws_session_token'] = Config.AWS_SESSION_TOKEN
            
        return boto3.client('s3', **client_params)
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise


@library_bp.route('/books', methods=['GET'])
def get_all_books():
    """
    GET /books - Fetch all books from S3
    
    Returns:
        JSON response with list of all books and their metadata
    """
    logger.info('Received request to GET /books')
    
    try:
        s3_client = get_s3_client()
        
        # List objects in the books/ prefix
        response = s3_client.list_objects_v2(
            Bucket=Config.S3_BUCKET_NAME,
            Prefix=Config.BOOKS_PREFIX
        )
        
        books = []
        for obj in response.get('Contents', []):
            # Skip directories
            if obj['Key'].endswith('/'):
                continue
                
            # Extract filename from full key
            filename = obj['Key'].replace(Config.BOOKS_PREFIX, '')
            
            # Parse filename to extract metadata (assuming format: "title_author_genre.pdf")
            try:
                name_parts = filename.replace('.pdf', '').split('_')
                if len(name_parts) >= 3:
                    title = name_parts[0].replace('-', ' ')
                    author = name_parts[1].replace('-', ' ')
                    genre = name_parts[2].replace('-', ' ')
                else:
                    title = filename.replace('.pdf', '')
                    author = "Unknown"
                    genre = "Unknown"
            except:
                title = filename.replace('.pdf', '')
                author = "Unknown"
                genre = "Unknown"
            
            books.append({
                'filename': filename,
                'title': title,
                'author': author,
                'genre': genre,
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat()
            })
        
        logger.info(f'Retrieved {len(books)} books from S3')
        
        return jsonify({
            'success': True,
            'count': len(books),
            'books': books
        }), 200
        
    except ClientError as e:
        logger.error(f'S3 error in get_all_books: {e}')
        return jsonify({
            'success': False,
            'error': 'S3 error',
            'message': 'Failed to retrieve books from S3'
        }), 500
        
    except NoCredentialsError:
        logger.error('AWS credentials not configured')
        return jsonify({
            'success': False,
            'error': 'Configuration error',
            'message': 'AWS credentials not properly configured'
        }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in get_all_books: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while retrieving books'
        }), 500


@library_bp.route('/book/<filename>', methods=['GET'])
def get_book_url(filename):
    """
    GET /book/<filename> - Generate pre-signed URL for a specific book
    
    Args:
        filename (str): The filename of the book
        
    Returns:
        JSON response with pre-signed URL
    """
    logger.info(f'Received request to GET /book/{filename}')
    
    try:
        s3_client = get_s3_client()
        
        # Construct the full S3 key
        s3_key = f"{Config.BOOKS_PREFIX}{filename}"
        
        # Generate pre-signed URL (expires in 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': Config.S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600  # 1 hour
        )
        
        logger.info(f'Generated pre-signed URL for {filename}')
        
        return jsonify({
            'success': True,
            'url': presigned_url,
            'expires_in': 3600,
            'filename': filename
        }), 200
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.warning(f'Book not found: {filename}')
            return jsonify({
                'success': False,
                'error': 'Book not found',
                'message': f'No book found with filename: {filename}'
            }), 404
        else:
            logger.error(f'S3 error in get_book_url: {e}')
            return jsonify({
                'success': False,
                'error': 'S3 error',
                'message': 'Failed to generate book URL'
            }), 500
            
    except NoCredentialsError:
        logger.error('AWS credentials not configured')
        return jsonify({
            'success': False,
            'error': 'Configuration error',
            'message': 'AWS credentials not properly configured'
        }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in get_book_url: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while generating book URL'
        }), 500


@library_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /health - Health check endpoint for the library service
    
    Returns:
        JSON response with service health status
    """
    logger.info('Received request to GET /health')
    
    try:
        # Test S3 connection
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=Config.S3_BUCKET_NAME)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'library-api',
            'aws_region': Config.AWS_REGION,
            's3_bucket': Config.S3_BUCKET_NAME
        }), 200
        
    except ClientError as e:
        logger.error(f'S3 error in health check: {e}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'S3 service error',
            'message': str(e)
        }), 503
        
    except NoCredentialsError:
        logger.error('AWS credentials not configured')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'Configuration error',
            'message': 'AWS credentials not properly configured'
        }), 503
        
    except Exception as e:
        logger.error(f'Unexpected error in health check: {e}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'Internal error',
            'message': str(e)
        }), 503