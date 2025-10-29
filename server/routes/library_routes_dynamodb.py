"""
Enhanced Library Routes with DynamoDB Integration
Handles book management with S3 + DynamoDB for metadata storage
"""

from flask import Blueprint, request, jsonify
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any
import json

from config import Config
from dynamodb_setup import DynamoDBManager
from enhanced_cover_extractor import cover_extractor

# Initialize the blueprint
library_bp = Blueprint('library', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize DynamoDB manager
db_manager = DynamoDBManager(region_name=Config.DYNAMODB_REGION)

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
    GET /books - Fetch all books from DynamoDB with S3 metadata
    Enhanced with DynamoDB for rich metadata storage
    """
    logger.info('Received request to GET /books')
    
    try:
        # Get books from DynamoDB
        books = db_manager.get_all_books()
        
        # If no books in DynamoDB, fallback to S3 and populate DynamoDB
        if not books:
            logger.info("No books found in DynamoDB, populating from S3...")
            books = populate_books_from_s3()
        
        # Add S3 file info to each book
        s3_client = get_s3_client()
        for book in books:
            try:
                # Get S3 object metadata
                s3_key = f"{Config.BOOKS_PREFIX}{book.get('filename', '')}"
                response = s3_client.head_object(
                    Bucket=Config.S3_BUCKET_NAME,
                    Key=s3_key
                )
                
                # Add S3 metadata
                book['s3_size'] = response.get('ContentLength', 0)
                book['s3_last_modified'] = response.get('LastModified', '').isoformat()
                book['s3_content_type'] = response.get('ContentType', 'application/pdf')
                
            except ClientError as e:
                logger.warning(f"Could not get S3 metadata for {book.get('filename')}: {e}")
                book['s3_size'] = 0
                book['s3_last_modified'] = ''
                book['s3_content_type'] = 'application/pdf'
        
        logger.info(f'Retrieved {len(books)} books from DynamoDB')
        
        return jsonify({
            'success': True,
            'count': len(books),
            'books': books,
            'source': 'dynamodb'
        }), 200
        
    except Exception as e:
        logger.error(f'Error in get_all_books: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve books'
        }), 500


def populate_books_from_s3() -> List[Dict[str, Any]]:
    """Populate DynamoDB with books from S3, using filename parsing as fallback"""
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
            
            # Try to get existing book from DynamoDB first
            existing_book = db_manager.get_book_by_filename(filename)
            if existing_book:
                books.append(existing_book)
                continue
            
            # Parse filename to extract metadata (using existing logic)
            book_metadata = parse_filename_metadata(filename)
            book_metadata.update({
                'filename': filename,
                's3_size': obj['Size'],
                's3_last_modified': obj['LastModified'].isoformat(),
                's3_content_type': 'application/pdf'
            })
            
            # Add to DynamoDB
            db_manager.add_book(book_metadata)
            books.append(book_metadata)
        
        logger.info(f'Populated {len(books)} books from S3 to DynamoDB')
        return books
        
    except Exception as e:
        logger.error(f'Error populating books from S3: {e}')
        return []


def parse_filename_metadata(filename: str) -> Dict[str, Any]:
    """Parse filename to extract metadata (simplified version of existing logic)"""
    import uuid
    from datetime import datetime
    
    try:
        name_without_ext = filename.replace('.pdf', '')
        
        # Simple parsing logic (you can enhance this)
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ')
            if len(parts) == 2:
                title = parts[0].strip()
                author = parts[1].strip()
            else:
                title = name_without_ext
                author = "Unknown"
        elif '_' in name_without_ext:
            parts = name_without_ext.split('_')
            if len(parts) >= 2:
                title = parts[0].replace('-', ' ')
                author = ' '.join(parts[1:]).replace('-', ' ')
            else:
                title = name_without_ext
                author = "Unknown"
        else:
            title = name_without_ext
            author = "Unknown"
        
        return {
            'book_id': str(uuid.uuid4()),
            'title': title,
            'author': author,
            'genre': 'General',
            'language': 'English',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.warning(f"Error parsing filename {filename}: {e}")
        return {
            'book_id': str(uuid.uuid4()),
            'title': filename.replace('.pdf', ''),
            'author': 'Unknown',
            'genre': 'General',
            'language': 'English',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }


@library_bp.route('/book/<book_id>', methods=['GET'])
def get_book_by_id(book_id: str):
    """
    GET /book/<book_id> - Get specific book by ID
    """
    logger.info(f'Received request to GET /book/{book_id}')
    
    try:
        book = db_manager.get_book_by_id(book_id)
        
        if not book:
            return jsonify({
                'success': False,
                'error': 'Book not found',
                'message': f'No book found with ID: {book_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'book': book
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting book {book_id}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve book'
        }), 500


@library_bp.route('/book/<filename>', methods=['GET'])
def get_book_url(filename: str):
    """
    GET /book/<filename> - Generate pre-signed URL for a specific book
    Enhanced with DynamoDB metadata lookup
    """
    logger.info(f'Received request to GET /book/{filename}')
    
    try:
        # Get book metadata from DynamoDB
        book = db_manager.get_book_by_filename(filename)
        
        # If book not in DynamoDB, create basic metadata from filename
        if not book:
            logger.info(f'Book {filename} not found in DynamoDB, creating basic metadata')
            # Parse filename to extract basic info
            name_without_ext = filename.replace('.pdf', '')
            if ' - ' in name_without_ext:
                parts = name_without_ext.split(' - ')
                title = parts[0].strip()
                author = parts[1].strip() if len(parts) > 1 else "Unknown"
            elif ' by ' in name_without_ext.lower():
                parts = name_without_ext.split(' by ')
                title = parts[0].strip()
                author = parts[1].strip() if len(parts) > 1 else "Unknown"
            else:
                title = name_without_ext
                author = "Unknown"
            
            book = {
                'filename': filename,
                'title': title,
                'author': author,
                'genre': 'General'
            }
        
        # Generate pre-signed URL
        s3_client = get_s3_client()
        s3_key = f"{Config.BOOKS_PREFIX}{filename}"
        
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
            'filename': filename,
            'book_metadata': book
        }), 200
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.warning(f'Book not found in S3: {filename}')
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
            'message': 'An unexpected error occurred'
        }), 500


@library_bp.route('/book/<filename>/details', methods=['GET'])
def get_book_details(filename: str):
    """
    GET /book/<filename>/details - Get book details and metadata
    """
    logger.info(f'Received request to GET /book/{filename}/details')
    
    try:
        # Get book metadata from DynamoDB
        book = db_manager.get_book_by_filename(filename)
        
        # If book not in DynamoDB, create basic metadata from filename
        if not book:
            logger.info(f'Book {filename} not found in DynamoDB, creating basic metadata')
            # Parse filename to extract basic info
            name_without_ext = filename.replace('.pdf', '')
            if ' - ' in name_without_ext:
                parts = name_without_ext.split(' - ')
                title = parts[0].strip()
                author = parts[1].strip() if len(parts) > 1 else "Unknown"
            elif ' by ' in name_without_ext.lower():
                parts = name_without_ext.split(' by ')
                title = parts[0].strip()
                author = parts[1].strip() if len(parts) > 1 else "Unknown"
            else:
                title = name_without_ext
                author = "Unknown"
            
            book = {
                'filename': filename,
                'title': title,
                'author': author,
                'genre': 'General',
                'language': 'English',
                'description': f'A digital copy of {title} by {author}',
                'publication_year': None,
                'isbn': None,
                'tags': [],
                'created_at': None,
                'updated_at': None
            }
        
        return jsonify({
            'success': True,
            'book': book
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting book details for {filename}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve book details'
        }), 500
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.warning(f'Book not found in S3: {filename}')
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


@library_bp.route('/books/search', methods=['GET'])
def search_books():
    """
    GET /books/search - Search books with various filters
    """
    logger.info('Received request to search books')
    
    try:
        # Get search parameters
        query = request.args.get('q', '')
        author = request.args.get('author', '')
        genre = request.args.get('genre', '')
        limit = int(request.args.get('limit', 50))
        
        books = []
        
        if author:
            books = db_manager.search_books_by_author(author)
        elif genre:
            books = db_manager.search_books_by_genre(genre)
        else:
            books = db_manager.get_all_books(limit=limit)
        
        # Simple text search if query provided
        if query:
            query_lower = query.lower()
            books = [
                book for book in books 
                if (query_lower in book.get('title', '').lower() or 
                    query_lower in book.get('author', '').lower() or
                    query_lower in book.get('description', '').lower())
            ]
        
        return jsonify({
            'success': True,
            'count': len(books),
            'books': books,
            'query': query,
            'filters': {
                'author': author,
                'genre': genre
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error searching books: {e}')
        return jsonify({
            'success': False,
            'error': 'Search error',
            'message': 'Failed to search books'
        }), 500


@library_bp.route('/books/<book_id>', methods=['PUT'])
def update_book_metadata(book_id: str):
    """
    PUT /books/<book_id> - Update book metadata
    """
    logger.info(f'Received request to update book {book_id}')
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'No data provided'
            }), 400
        
        # Remove fields that shouldn't be updated
        data.pop('book_id', None)
        data.pop('created_at', None)
        
        success = db_manager.update_book(book_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Book {book_id} updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update book metadata'
            }), 500
            
    except Exception as e:
        logger.error(f'Error updating book {book_id}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to update book'
        }), 500


@library_bp.route('/genres', methods=['GET'])
def get_genres():
    """
    GET /genres - Get all available book genres
    """
    logger.info('Received request to GET /genres')
    
    try:
        # Get all books and extract unique genres
        books = db_manager.get_all_books()
        genres = list(set(book.get('genre', 'General') for book in books))
        genres.sort()
        
        # Add common genres if not present
        common_genres = ['Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Biography', 'History']
        for genre in common_genres:
            if genre not in genres:
                genres.append(genre)
        
        return jsonify({
            'success': True,
            'genres': genres
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting genres: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve genres'
        }), 500


@library_bp.route('/bookmarks', methods=['GET'])
def get_bookmarks():
    """
    GET /bookmarks - Get user's bookmarked books
    Enhanced with DynamoDB for persistent storage
    """
    logger.info('Received request to GET /bookmarks')
    
    try:
        # Get user ID from request (you'll need to implement authentication)
        user_id = request.headers.get('X-User-ID', 'default-user')
        
        bookmark_items = db_manager.get_user_bookmarks(user_id)
        
        # Get full book details for each bookmark
        books = []
        for bookmark in bookmark_items:
            book = db_manager.get_book_by_id(bookmark['book_id'])
            if book:
                book['bookmarked_at'] = bookmark.get('date_added')
                books.append(book)
        
        return jsonify({
            'success': True,
            'bookmarks': books,
            'count': len(books)
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting bookmarks: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bookmarks'
        }), 500


@library_bp.route('/bookmarks/<book_id>', methods=['POST'])
def add_bookmark(book_id: str):
    """
    POST /bookmarks/<book_id> - Add a book to bookmarks
    """
    logger.info(f'Received request to POST /bookmarks/{book_id}')
    
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID', 'default-user')
        
        # Verify book exists
        book = db_manager.get_book_by_id(book_id)
        if not book:
            return jsonify({
                'success': False,
                'error': 'Book not found',
                'message': f'No book found with ID: {book_id}'
            }), 404
        
        success = db_manager.add_user_bookmark(user_id, book_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Book {book_id} added to bookmarks'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add bookmark'
            }), 500
            
    except Exception as e:
        logger.error(f'Error adding bookmark: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to add bookmark'
        }), 500


@library_bp.route('/bookmarks/<book_id>', methods=['DELETE'])
def remove_bookmark(book_id: str):
    """
    DELETE /bookmarks/<book_id> - Remove a book from bookmarks
    """
    logger.info(f'Received request to DELETE /bookmarks/{book_id}')
    
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID', 'default-user')
        
        success = db_manager.remove_user_bookmark(user_id, book_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Book {book_id} removed from bookmarks'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to remove bookmark'
            }), 500
            
    except Exception as e:
        logger.error(f'Error removing bookmark: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to remove bookmark'
        }), 500


@library_bp.route('/books/<book_id>/rate', methods=['POST'])
def rate_book(book_id: str):
    """
    POST /books/<book_id>/rate - Rate a book
    """
    logger.info(f'Received request to rate book {book_id}')
    
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Rating is required'
            }), 400
        
        rating = int(data['rating'])
        review = data.get('review', '')
        
        if rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': 'Invalid rating',
                'message': 'Rating must be between 1 and 5'
            }), 400
        
        # Get user ID from request
        user_id = request.headers.get('X-User-ID', 'default-user')
        
        success = db_manager.add_user_rating(user_id, book_id, rating, review)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Rating {rating} added for book {book_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add rating'
            }), 500
            
    except Exception as e:
        logger.error(f'Error rating book {book_id}: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to rate book'
        }), 500


@library_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /health - Health check endpoint for the library service
    Enhanced with DynamoDB health check
    """
    logger.info('Received request to GET /health')
    
    try:
        # Test S3 connection
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=Config.S3_BUCKET_NAME)
        
        # Test DynamoDB connection
        db_manager.get_books_table()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'library-api',
            'aws_region': Config.AWS_REGION,
            's3_bucket': Config.S3_BUCKET_NAME,
            'dynamodb_tables': {
                'books': Config.DYNAMODB_BOOKS_TABLE,
                'user_books': Config.DYNAMODB_USER_BOOKS_TABLE
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': 'Service error',
            'message': str(e)
        }), 503


@library_bp.route('/book/<filename>/cover', methods=['GET'])
def get_book_cover(filename: str):
    """
    GET /book/<filename>/cover - Get or generate cover image for a book
    
    Args:
        filename: The PDF filename
        
    Returns:
        JSON response with cover image URL
    """
    logger.info(f'Received request to GET /book/{filename}/cover')
    
    try:
        # Get cover URL (extract if necessary)
        cover_url = cover_extractor.get_cover_url(filename)
        
        if not cover_url:
            return jsonify({
                'success': False,
                'error': 'Cover not available',
                'message': f'Could not generate cover for {filename}'
            }), 404
        
        return jsonify({
            'success': True,
            'cover_url': cover_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting cover for {filename}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to get book cover'
        }), 500


@library_bp.route('/book/<filename>/cover/extract', methods=['POST'])
def extract_book_cover(filename: str):
    """
    POST /book/<filename>/cover/extract - Force extract cover image for a book
    
    Args:
        filename: The PDF filename
        
    Returns:
        JSON response with cover image URL
    """
    logger.info(f'Received request to POST /book/{filename}/cover/extract')
    
    try:
        # Force extract cover (even if it exists)
        cover_url = cover_extractor.extract_cover_from_s3(filename)
        
        if not cover_url:
            return jsonify({
                'success': False,
                'error': 'Cover extraction failed',
                'message': f'Could not extract cover for {filename}'
            }), 500
        
        return jsonify({
            'success': True,
            'cover_url': cover_url,
            'filename': filename,
            'message': 'Cover extracted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f'Error extracting cover for {filename}: {e}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to extract book cover'
        }), 500
