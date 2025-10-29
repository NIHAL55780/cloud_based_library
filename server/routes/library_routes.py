"""
Library Routes for Cloud-Based Digital Library Backend
Handles book management and S3 operations
"""

from flask import Blueprint, request, jsonify
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime

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


def format_error_response(error_type, message, status_code=500, **kwargs):
    """
    Standardized error response format
    """
    return jsonify({
        'success': False,
        'error': error_type,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        **kwargs
    }), status_code


@library_bp.route('/books', methods=['GET'])
def get_all_books():
    """
    GET /books - Fetch all books from DynamoDB (not S3!)
    
    Returns:
        JSON response with list of all books and their metadata
    """
    logger.info('Received request to GET /books')
    
    try:
        # Import DynamoDB helper
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books from DynamoDB
        books = db_helper.get_all_books()
        
        # Format books data - READ FROM DYNAMODB
        formatted_books = []
        for item in books:
            book = {
                'title': item.get('Title', ''),
                'author': item.get('Author', ''),
                'genre': item.get('Genre'),  # ← Read Genre from DynamoDB (Capital G)
                'filename': item.get('Title', ''),  # Use Title as filename
                'description': item.get('Description', ''),
                'book_id': item.get('BookID', '')
            }
            
            # Only add books that have a genre
            if book['genre']:
                formatted_books.append(book)
        
        logger.info(f'Retrieved {len(formatted_books)} books from DynamoDB')
        
        return jsonify({
            'success': True,
            'count': len(formatted_books),
            'books': formatted_books,
            'cached': False
        }), 200
        
    except Exception as e:
        logger.error(f'Error fetching books: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@library_bp.route('/debug/test-book/<bookid>', methods=['GET'])
def debug_test_book_by_id(bookid):
    """
    Debug endpoint to test getting a book by BookID
    """
    try:
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        book = db_helper.get_book_by_id(bookid)
        
        if book:
            return jsonify({
                'success': True,
                'book': book,
                'message': f'Found book with BookID: {bookid}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'No book found with BookID: {bookid}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/debug/test-filename/<filename>', methods=['GET'])
def debug_test_filename(filename):
    """
    Debug endpoint to test filename parsing and matching
    """
    from urllib.parse import unquote
    from dynamodb_helper import SimpleDynamoDBHelper
    
    decoded_filename = unquote(filename)
    logger.info(f'Testing filename: {decoded_filename}')
    
    try:
        db_helper = SimpleDynamoDBHelper()
        
        # Parse the filename
        parsed_data = db_helper._parse_filename_to_title_author(decoded_filename)
        title = parsed_data.get('title')
        author = parsed_data.get('author')
        
        logger.info(f'Parsed - Title: "{title}", Author: "{author}"')
        
        # Get all books to see what we're matching against
        all_books = db_helper.get_all_books()
        
        # Try to find matches
        matches = []
        for book in all_books:
            book_title = book.get('Title', '')
            book_author = book.get('Author', '')
            
            title_match = title and title.lower() in book_title.lower()
            author_match = author and author.lower() in book_author.lower()
            
            if title_match or author_match:
                matches.append({
                    'BookID': book.get('BookID'),
                    'Title': book_title,
                    'Author': book_author,
                    'title_match': title_match,
                    'author_match': author_match
                })
        
        return jsonify({
            'success': True,
            'original_filename': filename,
            'decoded_filename': decoded_filename,
            'parsed_title': title,
            'parsed_author': author,
            'total_books': len(all_books),
            'matches': matches,
            'message': f'Found {len(matches)} potential matches'
        }), 200
        
    except Exception as e:
        logger.error(f'Error in debug_test_filename: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/debug/filenames', methods=['GET'])
def debug_filenames():
    """
    Debug endpoint to see all filenames in the table
    """
    logger.info('Received debug request to see all filenames')
    
    try:
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books from DynamoDB
        books = db_helper.get_all_books()
        
        # Since there's no filename field, let's show Title and Author combinations
        book_info = []
        if books:
            for book in books:
                title = book.get('Title', 'Unknown')
                author = book.get('Author', 'Unknown')
                book_info.append(f"{title} by {author}")
        else:
            book_info = ['NO_BOOKS_FOUND']
        
        logger.info(f'Found {len(book_info)} books in BookMetaData table')
        
        return jsonify({
            'success': True,
            'count': len(book_info),
            'books': book_info,
            'message': f'Found {len(book_info)} books in BookMetaData table'
        }), 200
        
    except Exception as e:
        logger.error(f'Error in debug_filenames: {e}')
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve filenames from BookMetaData table'
        }), 500


@library_bp.route('/debug/books', methods=['GET'])
def debug_books():
    """
    Debug endpoint to see what's in the BookMetaData table
    """
    logger.info('Received debug request to see all books')
    
    try:
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books from DynamoDB
        books = db_helper.get_all_books()
        
        logger.info(f'Found {len(books)} books in BookMetaData table')
        
        return jsonify({
            'success': True,
            'count': len(books),
            'books': books,
            'message': f'Found {len(books)} books in BookMetaData table'
        }), 200
        
    except Exception as e:
        logger.error(f'Error in debug_books: {e}')
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve books from BookMetaData table'
        }), 500


@library_bp.route('/book/<filename>/details', methods=['GET'])
def get_book_details(filename):
    """
    GET /book/<filename>/details - Get detailed metadata for a specific book
    
    Args:
        filename (str): The filename of the book
        
    Returns:
        JSON response with book metadata from DynamoDB
    """
    from urllib.parse import unquote
    
    # Decode URL encoding
    decoded_filename = unquote(filename)
    logger.info(f'Received request to GET /book/{filename}/details')
    logger.info(f'Original filename: {filename}')
    logger.info(f'Decoded filename: {decoded_filename}')
    
    try:
        # Import DynamoDB helper
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        logger.info(f'Looking for book with filename: {decoded_filename}')
        
        # First, let's see what books are actually in the table
        all_books = db_helper.get_all_books()
        logger.info(f'Total books in table: {len(all_books)}')
        if all_books:
            logger.info('Sample books in table:')
            for i, book in enumerate(all_books[:5]):  # Show first 5 books
                title = book.get('Title', 'NO_TITLE')
                author = book.get('Author', 'NO_AUTHOR')
                logger.info(f'  {i+1}. "{title}" by "{author}"')
        
        # Get book details from DynamoDB using decoded filename
        book_details = db_helper.get_book_by_filename(decoded_filename)
        
        logger.info(f'Book lookup result: {book_details is not None}')
        if book_details:
            logger.info(f'Found book: {book_details.get("title", "Unknown")} by {book_details.get("author", "Unknown")}')
        else:
            logger.warning(f'No book found with filename: {filename}')
        
        if not book_details:
            return jsonify({
                'success': False,
                'error': 'Book not found',
                'message': f'No book found with filename: {decoded_filename}',
                'debug_info': {
                    'original_filename': filename,
                    'decoded_filename': decoded_filename,
                    'table_name': Config.DYNAMODB_BOOKS_TABLE
                }
            }), 404
        
        # Add S3 file info
        try:
            s3_client = get_s3_client()
            s3_key = f"{Config.BOOKS_PREFIX}{decoded_filename}"
            response = s3_client.head_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=s3_key
            )
            
            book_details['s3_size'] = response.get('ContentLength', 0)
            book_details['s3_last_modified'] = response.get('LastModified', '').isoformat()
            book_details['s3_content_type'] = response.get('ContentType', 'application/pdf')
            
        except ClientError as e:
            logger.warning(f"Could not get S3 metadata for {filename}: {e}")
            book_details['s3_size'] = 0
            book_details['s3_last_modified'] = ''
            book_details['s3_content_type'] = 'application/pdf'
        
        logger.info(f'Retrieved book details for {filename}')
        logger.info(f'Book details structure: {list(book_details.keys()) if book_details else "None"}')
        
        return jsonify({
            'success': True,
            'book': book_details
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting book details for {filename}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve book details'
        }), 500


@library_bp.route('/book/<path:filename>', methods=['GET'])
def get_book_url(filename):
    """
    GET /book/<filename> - Generate pre-signed URL for a specific book
    
    Args:
        filename (str): The filename of the book
        
    Returns:
        JSON response with pre-signed URL
    """
    from urllib.parse import unquote
    
    # Decode URL encoding
    decoded_filename = unquote(filename)
    logger.info(f'Received request to GET /book/{decoded_filename}')
    
    try:
        s3_client = get_s3_client()
        
        # Construct the full S3 key - NO SPACE after books/
        # Also add .pdf extension if not present
        if not decoded_filename.endswith('.pdf'):
            decoded_filename = f"{decoded_filename}.pdf"
        
        s3_key = f"books/{decoded_filename}"  # No Config.BOOKS_PREFIX with extra space
        
        logger.info(f'Looking for S3 key: {s3_key}')
        
        # First, check if the file exists in S3
        try:
            s3_client.head_object(Bucket=Config.S3_BUCKET_NAME, Key=s3_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f'File not found in S3: {s3_key}')
                return jsonify({
                    'success': False,
                    'error': 'Book not found',
                    'message': f'No book found with filename: {decoded_filename}',
                    'debug': {
                        's3_key': s3_key,
                        'bucket': Config.S3_BUCKET_NAME
                    }
                }), 404
            raise
        
        # Generate pre-signed URL (expires in 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': Config.S3_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': f'inline; filename="{decoded_filename}"',
                'ResponseContentType': 'application/pdf'
            },
            ExpiresIn=3600  # 1 hour
        )
        
        logger.info(f'Generated pre-signed URL for {decoded_filename}')
        
        return jsonify({
            'success': True,
            'url': presigned_url,
            'expires_in': 3600,
            'filename': decoded_filename
        }), 200
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f'S3 error in get_book_url: {e}')
        return jsonify({
            'success': False,
            'error': 'S3 error',
            'message': str(e),
            'error_code': error_code
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
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@library_bp.route('/genres', methods=['GET'])
def get_genres():
    """
    GET /genres - Get all available book genres from DynamoDB
    
    Returns:
        JSON response with list of all available genres
    """
    logger.info('Received request to GET /genres')
    
    try:
        # Import DynamoDB helper
        from dynamodb_helper import SimpleDynamoDBHelper
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books from DynamoDB
        books = db_helper.get_all_books()
        
        # Extract unique genres (Capital G from DynamoDB)
        genres = set()
        for book in books:
            genre = book.get('Genre')  # ← Capital G
            if genre:
                genres.add(genre)
        
        sorted_genres = ['All Genres'] + sorted(list(genres))
        
        logger.info(f'Found {len(sorted_genres)} unique genres')
        
        return jsonify({
            'success': True,
            'genres': sorted_genres,
            'count': len(sorted_genres)
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting genres: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve genres',
            'message': str(e)
        }), 500


@library_bp.route('/bookmarks', methods=['GET'])
def get_bookmarks():
    """
    GET /bookmarks - Get user's bookmarked books
    
    Returns:
        JSON response with list of bookmarked books
    """
    logger.info('Received request to GET /bookmarks')
    
    try:
        # For now, return empty list - in production, this would check user authentication
        # and retrieve bookmarks from a database
        return jsonify({
            'success': True,
            'bookmarks': []
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting bookmarks: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bookmarks'
        }), 500


@library_bp.route('/bookmarks/<filename>', methods=['POST'])
def add_bookmark(filename):
    """
    POST /bookmarks/<filename> - Add a book to bookmarks
    
    Args:
        filename: Name of the book file to bookmark
        
    Returns:
        JSON response indicating success/failure
    """
    logger.info(f'Received request to POST /bookmarks/{filename}')
    
    try:
        # For now, just return success - in production, this would save to database
        # and verify the book exists in S3
        return jsonify({
            'success': True,
            'message': f'Book {filename} added to bookmarks'
        }), 200
        
    except Exception as e:
        logger.error(f'Error adding bookmark: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to add bookmark'
        }), 500


@library_bp.route('/bookmarks/<filename>', methods=['DELETE'])
def remove_bookmark(filename):
    """
    DELETE /bookmarks/<filename> - Remove a book from bookmarks
    
    Args:
        filename: Name of the book file to remove from bookmarks
        
    Returns:
        JSON response indicating success/failure
    """
    logger.info(f'Received request to DELETE /bookmarks/{filename}')
    
    try:
        # For now, just return success - in production, this would remove from database
        return jsonify({
            'success': True,
            'message': f'Book {filename} removed from bookmarks'
        }), 200
        
    except Exception as e:
        logger.error(f'Error removing bookmark: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to remove bookmark'
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