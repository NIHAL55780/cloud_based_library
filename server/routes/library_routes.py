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
            
            # Parse filename to extract metadata with intelligent pattern recognition
            try:
                name_without_ext = filename.replace('.pdf', '')
                genre = "General"  # Default genre
                
                # Common author name patterns to help identify authors
                common_authors = [
                    'Arundhati Roy', 'A.P.J. Abdul Kalam', 'Abdul Kalam', 'Kalam',
                    'Norman Vincent Peale', 'Vincent Peale', 'Peale',
                    'J.K. Rowling', 'Rowling',
                    'George Orwell', 'Orwell',
                    'Harper Lee', 'Lee',
                    'F. Scott Fitzgerald', 'Fitzgerald',
                    'Ernest Hemingway', 'Hemingway',
                    'Mark Twain', 'Twain',
                    'Charles Dickens', 'Dickens',
                    'Jane Austen', 'Austen',
                    'Leo Tolstoy', 'Tolstoy',
                    'Fyodor Dostoevsky', 'Dostoevsky',
                    'Gabriel Garcia Marquez', 'Marquez',
                    'Maya Angelou', 'Angelou',
                    'Toni Morrison', 'Morrison',
                    'Chimamanda Ngozi Adichie', 'Adichie',
                    'Arundhati', 'Roy'
                ]
                
                # Common genre categories
                genre_keywords = {
                    'mystery': ['mystery', 'detective', 'crime', 'thriller', 'suspense', 'sherlock', 'holmes'],
                    'inspiration': ['inspiration', 'motivation', 'self-help', 'positive', 'thinking', 'mindset', 'success'],
                    'romance': ['romance', 'love', 'relationship', 'dating', 'marriage'],
                    'fiction': ['fiction', 'novel', 'story', 'tale', 'adventure'],
                    'biography': ['biography', 'autobiography', 'memoir', 'life', 'story'],
                    'science': ['science', 'technology', 'research', 'discovery', 'innovation'],
                    'philosophy': ['philosophy', 'wisdom', 'knowledge', 'truth', 'meaning'],
                    'history': ['history', 'historical', 'past', 'ancient', 'war'],
                    'fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'mythical'],
                    'horror': ['horror', 'scary', 'ghost', 'supernatural', 'frightening'],
                    'comedy': ['comedy', 'humor', 'funny', 'joke', 'laugh'],
                    'drama': ['drama', 'tragedy', 'serious', 'emotional', 'intense']
                }
                
                def is_likely_author(text):
                    """Check if text is likely an author name"""
                    text_lower = text.lower()
                    return any(author.lower() in text_lower for author in common_authors)
                
                def is_likely_title(text):
                    """Check if text is likely a book title"""
                    # Titles are usually longer and contain common words
                    words = text.split()
                    if len(words) < 2:
                        return False
                    # Common title words
                    title_words = ['the', 'of', 'and', 'in', 'a', 'an', 'to', 'for', 'with', 'by']
                    return any(word.lower() in title_words for word in words)
                
                def detect_genre(text):
                    """Detect genre based on keywords in the text"""
                    text_lower = text.lower()
                    for genre, keywords in genre_keywords.items():
                        if any(keyword in text_lower for keyword in keywords):
                            return genre.title()
                    return "General"
                
                # Handle different filename patterns
                if ' - ' in name_without_ext:
                    # Pattern: "Author - Title" or "Title - Author"
                    parts = name_without_ext.split(' - ')
                    if len(parts) == 2:
                        first_part = parts[0].strip()
                        second_part = parts[1].strip()
                        
                        # Intelligent detection based on content
                        if is_likely_author(first_part) and not is_likely_author(second_part):
                            author = first_part
                            title = second_part
                        elif is_likely_author(second_part) and not is_likely_author(first_part):
                            title = first_part
                            author = second_part
                        elif is_likely_title(first_part) and not is_likely_title(second_part):
                            title = first_part
                            author = second_part
                        else:
                            # Default: assume first part is title, second is author
                            title = first_part
                            author = second_part
                        
                        # Detect genre from the full filename
                        genre = detect_genre(name_without_ext)
                    else:
                        title = name_without_ext
                        author = "Unknown"
                        genre = detect_genre(name_without_ext)
                        
                elif '_' in name_without_ext:
                    # Pattern: "title_author" or "title_author_genre"
                    parts = name_without_ext.split('_')
                    if len(parts) >= 2:
                        # Try to identify which part is author vs title
                        if is_likely_author(parts[1]):
                            title = parts[0].replace('-', ' ')
                            author = parts[1].replace('-', ' ')
                        elif len(parts) >= 3:
                            # Likely format: title_author_genre
                            title = parts[0].replace('-', ' ')
                            author = ' '.join(parts[1:-1]).replace('-', ' ')
                            genre = parts[-1].replace('-', ' ')
                        else:
                            # For simple two-part patterns, try to detect author
                            potential_author = parts[1].replace('-', ' ')
                            if is_likely_author(potential_author):
                                title = parts[0].replace('-', ' ')
                                author = potential_author
                            else:
                                # Default: first part is title, second is author
                                title = parts[0].replace('-', ' ')
                                author = potential_author
                        
                        # If genre wasn't explicitly set, detect it
                        if genre == "General":
                            genre = detect_genre(name_without_ext)
                    else:
                        title = name_without_ext
                        author = "Unknown"
                        genre = detect_genre(name_without_ext)
                        
                elif ' by ' in name_without_ext.lower():
                    # Pattern: "Title by Author"
                    parts = name_without_ext.split(' by ')
                    if len(parts) == 2:
                        title = parts[0].strip()
                        author = parts[1].strip()
                    else:
                        title = name_without_ext
                        author = "Unknown"
                    
                    # Detect genre from the full filename
                    genre = detect_genre(name_without_ext)
                        
                elif ',' in name_without_ext:
                    # Pattern: "Author, Title" or "Title, Author"
                    parts = name_without_ext.split(',')
                    if len(parts) == 2:
                        first_part = parts[0].strip()
                        second_part = parts[1].strip()
                        
                        if is_likely_author(first_part):
                            author = first_part
                            title = second_part
                        else:
                            title = first_part
                            author = second_part
                    else:
                        title = name_without_ext
                        author = "Unknown"
                    
                    # Detect genre from the full filename
                    genre = detect_genre(name_without_ext)
                else:
                    # Single word or simple title - try to extract meaningful title
                    title = name_without_ext
                    author = "Unknown"
                    genre = detect_genre(name_without_ext)
                    
            except Exception as e:
                logger.warning(f"Error parsing filename {filename}: {e}")
                title = filename.replace('.pdf', '')
                author = "Unknown"
                genre = "General"
            
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


@library_bp.route('/genres', methods=['GET'])
def get_genres():
    """
    GET /genres - Get all available book genres
    
    Returns:
        JSON response with list of all available genres
    """
    logger.info('Received request to GET /genres')
    
    try:
        # Get all available genres from the genre_keywords
        genres = [
            'All Genres', 'Mystery', 'Inspiration', 'Romance', 'Fiction', 
            'Biography', 'Science', 'Philosophy', 'History', 'Fantasy', 
            'Horror', 'Comedy', 'Drama', 'General'
        ]
        
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