"""
Library Routes for Cloud-Based Digital Library Backend
Handles book management, file uploads to S3, and DynamoDB operations
"""

from flask import Blueprint, request, jsonify
import logging
import uuid
import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from config import Config

# Initialize the blueprint
library_bp = Blueprint('library', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Allowed file extensions for book uploads
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_s3_client():
    """Initialize and return S3 client with credentials from environment"""
    try:
        if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
            raise NoCredentialsError("AWS credentials not configured")
        return boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise


def get_dynamodb_resource():
    """Initialize and return DynamoDB resource with credentials from environment"""
    try:
        if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
            raise NoCredentialsError("AWS credentials not configured")
        return boto3.resource(
            'dynamodb',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise


def get_books_table():
    """Get the DynamoDB table for books metadata"""
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(Config.DYNAMODB_TABLE_NAME)


@library_bp.route('/books', methods=['GET'])
def get_all_books():
    """
    GET /books - Fetch all books from DynamoDB
    
    Returns:
        JSON response with list of all books and their metadata
    """
    logger.info('Received request to GET /books')
    
    try:
        table = get_books_table()
        
        # Scan the table to get all items
        response = table.scan()
        books = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            logger.debug('Scanning next page for books')
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            books.extend(response.get('Items', []))
        
        logger.info(f'Retrieved {len(books)} books from DynamoDB')
        
        return jsonify({
            'success': True,
            'count': len(books),
            'books': books
        }), 200
        
    except ClientError as e:
        logger.error(f'DynamoDB error in get_all_books: {e}')
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'Failed to retrieve books from database'
        }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in get_all_books: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while retrieving books'
        }), 500


@library_bp.route('/books/<book_id>', methods=['GET'])
def get_book_by_id(book_id):
    """
    GET /books/<book_id> - Fetch a single book by its BookID
    
    Args:
        book_id (str): The unique identifier of the book
        
    Returns:
        JSON response with book metadata or error message
    """
    logger.info(f'Received request to GET /books/{book_id}')
    
    try:
        table = get_books_table()
        
        # Get item by primary key (BookID)
        response = table.get_item(Key={'BookID': book_id})
        
        if 'Item' not in response:
            logger.warning(f'Book with ID {book_id} not found')
            return jsonify({
                'success': False,
                'error': 'Book not found',
                'message': f'No book found with ID: {book_id}'
            }), 404
        
        book = response['Item']
        logger.info(f'Retrieved book: {book.get("Title", "Unknown")}')
        
        return jsonify({
            'success': True,
            'book': book
        }), 200
        
    except ClientError as e:
        logger.error(f'DynamoDB error in get_book_by_id: {e}')
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'Failed to retrieve book from database'
        }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in get_book_by_id: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while retrieving the book'
        }), 500


@library_bp.route('/upload', methods=['POST'])
def upload_book():
    """
    POST /upload - Upload a new book file to S3 and add metadata to DynamoDB
    
    Expected form data:
        - file: PDF or JPG file
        - title: Book title
        - author: Book author
        - genre: Book genre
        - description: Book description (optional)
    
    Returns:
        JSON response with upload status and book metadata
    """
    logger.info('Received request to POST /upload')
    
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            logger.warning('No file provided in upload request')
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Please provide a file to upload'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning('No file selected for upload')
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            logger.warning(f'Invalid file type: {file.filename}')
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Only PDF and JPG files are allowed'
            }), 400
        
        # Get form data
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        genre = request.form.get('genre', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate required fields
        if not title or not author or not genre:
            logger.warning('Missing required fields in upload request')
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Title, author, and genre are required'
            }), 400
        
        # Generate unique book ID and secure filename
        book_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        secure_name = secure_filename(f"{book_id}.{file_extension}")
        
        # Initialize S3 client
        s3_client = get_s3_client()
        
        # Upload file to S3
        try:
            s3_client.upload_fileobj(
                file,
                Config.S3_BUCKET_NAME,
                secure_name,
                ExtraArgs={
                    'ContentType': 'application/pdf' if file_extension == 'pdf' else 'image/jpeg',
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Generate public S3 URL
            s3_url = f"https://{Config.S3_BUCKET_NAME}.s3.{Config.AWS_REGION}.amazonaws.com/{secure_name}"
            
            logger.info(f'Successfully uploaded file to S3: {s3_url}')
            
        except ClientError as e:
            logger.error(f'S3 upload error: {e}')
            return jsonify({
                'success': False,
                'error': 'Upload failed',
                'message': 'Failed to upload file to cloud storage'
            }), 500
        
        # Prepare metadata for DynamoDB
        upload_date = datetime.now(timezone.utc).isoformat()
        
        book_metadata = {
            'BookID': book_id,
            'Title': title,
            'Author': author,
            'Genre': genre,
            'S3URL': s3_url,
            'UploadDate': upload_date
        }
        
        # Add description if provided
        if description:
            book_metadata['Description'] = description
        
        # Save metadata to DynamoDB
        try:
            table = get_books_table()
            table.put_item(Item=book_metadata)
            
            logger.info(f'Successfully saved book metadata to DynamoDB: {book_id}')
            
        except ClientError as e:
            logger.error(f'DynamoDB error during metadata save: {e}')
            # If DynamoDB save fails, we should ideally clean up the S3 file
            # For now, we'll just log the error and return a partial success
            return jsonify({
                'success': False,
                'error': 'Metadata save failed',
                'message': 'File uploaded but metadata could not be saved',
                's3_url': s3_url
            }), 500
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Book uploaded successfully',
            'book_id': book_id,
            'book': book_metadata
        }), 201
        
    except NoCredentialsError:
        logger.error('AWS credentials not configured')
        return jsonify({
            'success': False,
            'error': 'Configuration error',
            'message': 'AWS credentials not properly configured'
        }), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in upload_book: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during upload'
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
        # Test DynamoDB connection
        table = get_books_table()
        table.load()  # This will raise an exception if table doesn't exist or can't be accessed
        
        # Test S3 connection
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=Config.S3_BUCKET_NAME)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'library-api',
            'aws_region': Config.AWS_REGION,
            's3_bucket': Config.S3_BUCKET_NAME,
            'dynamodb_table': Config.DYNAMODB_TABLE_NAME
        }), 200
        
    except ClientError as e:
        logger.error(f'AWS service error in health check: {e}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'AWS service error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f'Unexpected error in health check: {e}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'Internal error',
            'message': str(e)
        }), 503