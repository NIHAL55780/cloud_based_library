"""
Library routes for book-related operations
Handles book listing, retrieval, and metadata
"""

from flask import Blueprint, jsonify, send_file, request
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
import os
from config import Config

# Initialize Blueprint
library_bp = Blueprint('library', __name__)
logger = logging.getLogger(__name__)

# Initialize S3 client with session token support
def get_s3_client():
    """Create S3 client with proper credentials"""
    try:
        session_token = os.getenv('AWS_SESSION_TOKEN')
        
        if session_token:
            # Use temporary credentials with session token
            s3 = boto3.client(
                's3',
                region_name=Config.AWS_REGION,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=session_token
            )
        else:
            # Use permanent credentials
            s3 = boto3.client(
                's3',
                region_name=Config.AWS_REGION,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        
        logger.info(f"S3 client initialized for region: {Config.AWS_REGION}")
        return s3
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {str(e)}")
        return None

BUCKET_NAME = Config.S3_BUCKET_NAME

@library_bp.route('/books', methods=['GET'])
def get_books():
    """Get list of all books from S3 bucket"""
    try:
        s3_client = get_s3_client()
        if not s3_client:
            logger.error("S3 client not initialized")
            return jsonify({'error': 'S3 service unavailable', 'details': 'Failed to initialize S3 client'}), 500
            
        logger.info(f"Fetching books from bucket: {BUCKET_NAME}")
        
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            logger.warning("No books found in bucket")
            return jsonify([]), 200
        
        books = []
        for obj in response['Contents']:
            filename = obj['Key']
            
            # Skip non-book files
            if not filename.lower().endswith(('.pdf', '.epub', '.mobi')):
                continue
            
            # Extract book info from filename
            book_name = filename.rsplit('.', 1)[0]
            parts = book_name.split(' by ')
            
            try:
                # Try to get metadata from S3 object metadata
                metadata_response = s3_client.head_object(Bucket=BUCKET_NAME, Key=filename)
                metadata = metadata_response.get('Metadata', {})
                
                title = metadata.get('title', parts[0] if len(parts) > 0 else book_name)
                author = metadata.get('author', parts[1] if len(parts) > 1 else 'Unknown')
                genre = metadata.get('genre', metadata.get('subject', 'General'))
                
            except Exception as meta_error:
                logger.warning(f"Could not fetch metadata for {filename}: {str(meta_error)}")
                # Use filename parsing as fallback
                title = parts[0] if len(parts) > 0 else book_name
                author = parts[1] if len(parts) > 1 else 'Unknown'
                genre = 'General'
            
            books.append({
                'filename': filename,
                'title': title,
                'author': author,
                'genre': genre,
                'size': obj.get('Size', 0),
                'lastModified': obj.get('LastModified').isoformat() if obj.get('LastModified') else None
            })
        
        logger.info(f"Successfully fetched {len(books)} books")
        return jsonify(books), 200
        
    except NoCredentialsError:
        logger.error("AWS credentials not found or expired")
        return jsonify({
            'error': 'AWS credentials error',
            'details': 'Credentials not found or session token expired. Please update your AWS credentials.'
        }), 500
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"AWS S3 Error ({error_code}): {error_msg}")
        return jsonify({
            'error': 'Failed to fetch books from S3',
            'code': error_code,
            'message': error_msg
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_books: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@library_bp.route('/book/<path:filename>', methods=['GET'])
def get_book(filename):
    """Get a specific book file or its metadata"""
    try:
        s3_client = get_s3_client()
        if not s3_client:
            return jsonify({'error': 'S3 service unavailable'}), 500
            
        # Check if requesting metadata
        if request.args.get('metadata') == 'true':
            return get_book_metadata(filename, s3_client)
        
        logger.info(f"Generating presigned URL for: {filename}")
        
        # Generate presigned URL (valid for 1 hour)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': filename
            },
            ExpiresIn=3600
        )
        
        logger.info(f"Successfully generated URL for {filename}")
        return jsonify({'url': url}), 200
        
    except ClientError as e:
        logger.error(f"AWS S3 Error for {filename}: {str(e)}")
        return jsonify({'error': 'Book not found', 'details': str(e)}), 404
    except Exception as e:
        logger.error(f"Error retrieving book {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve book', 'details': str(e)}), 500

def get_book_metadata(filename, s3_client):
    """Get detailed metadata for a specific book"""
    try:
        logger.info(f"Fetching metadata for: {filename}")
        
        # Get object metadata from S3
        response = s3_client.head_object(Bucket=BUCKET_NAME, Key=filename)
        metadata = response.get('Metadata', {})
        
        # Extract book info from filename
        book_name = filename.rsplit('.', 1)[0]
        parts = book_name.split(' by ')
        extension = filename.rsplit('.', 1)[1] if '.' in filename else 'unknown'
        
        title = metadata.get('title', parts[0] if len(parts) > 0 else book_name)
        author = metadata.get('author', parts[1] if len(parts) > 1 else 'Unknown')
        genre = metadata.get('genre', metadata.get('subject', 'General'))
        
        book_data = {
            'filename': filename,
            'title': title,
            'author': author,
            'genre': genre,
            'description': metadata.get('description', f'A captivating {genre.lower()} book by {author}.'),
            'size': response.get('ContentLength', 0),
            'contentType': response.get('ContentType', f'application/{extension}'),
            'lastModified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
            'bookId': filename.replace('.', '_').replace(' ', '_').replace('/', '_').lower()[:50]
        }
        
        logger.info(f"Successfully fetched metadata for {filename}")
        return jsonify(book_data), 200
        
    except ClientError as e:
        logger.error(f"AWS S3 Error for {filename}: {str(e)}")
        return jsonify({'error': 'Book not found', 'details': str(e)}), 404
    except Exception as e:
        logger.error(f"Error fetching metadata for {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch metadata', 'details': str(e)}), 500

@library_bp.route('/genres', methods=['GET'])
def get_genres():
    """Get list of all unique genres"""
    try:
        s3_client = get_s3_client()
        if not s3_client:
            return jsonify({'error': 'S3 service unavailable'}), 500
            
        logger.info("Fetching genres")
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            return jsonify([]), 200
        
        genres = set()
        for obj in response['Contents']:
            filename = obj['Key']
            if not filename.lower().endswith(('.pdf', '.epub', '.mobi')):
                continue
            
            try:
                metadata_response = s3_client.head_object(Bucket=BUCKET_NAME, Key=filename)
                metadata = metadata_response.get('Metadata', {})
                genre = metadata.get('genre', metadata.get('subject', 'General'))
                genres.add(genre)
            except Exception as e:
                logger.warning(f"Could not get genre for {filename}: {str(e)}")
                genres.add('General')
        
        genre_list = sorted(list(genres))
        logger.info(f"Found {len(genre_list)} genres")
        return jsonify(genre_list), 200
        
    except ClientError as e:
        logger.error(f"AWS S3 Error fetching genres: {str(e)}")
        return jsonify({'error': 'Failed to fetch genres', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Error fetching genres: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch genres', 'details': str(e)}), 500

@library_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    s3_client = get_s3_client()
    s3_status = 'connected' if s3_client else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'service': 'library',
        's3': s3_status,
        'bucket': BUCKET_NAME
    }), 200