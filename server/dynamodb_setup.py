"""
DynamoDB Setup and Configuration for Digital Library
Creates tables and manages DynamoDB operations
"""

import boto3
from botocore.exceptions import ClientError
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DynamoDBManager:
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize DynamoDB client"""
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.client = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
        
    def create_tables(self):
        """Create DynamoDB tables for the digital library"""
        
        # Books table
        books_table_config = {
            'TableName': 'DigitalLibrary-Books',
            'KeySchema': [
                {'AttributeName': 'book_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'book_id', 'AttributeType': 'S'},
                {'AttributeName': 'author', 'AttributeType': 'S'},
                {'AttributeName': 'title', 'AttributeType': 'S'},
                {'AttributeName': 'genre', 'AttributeType': 'S'},
                {'AttributeName': 'publication_year', 'AttributeType': 'N'},
                {'AttributeName': 'filename', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'AuthorIndex',
                    'KeySchema': [
                        {'AttributeName': 'author', 'KeyType': 'HASH'},
                        {'AttributeName': 'title', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'GenreIndex',
                    'KeySchema': [
                        {'AttributeName': 'genre', 'KeyType': 'HASH'},
                        {'AttributeName': 'publication_year', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'FilenameIndex',
                    'KeySchema': [
                        {'AttributeName': 'filename', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        # User-Book interactions table
        user_books_table_config = {
            'TableName': 'DigitalLibrary-UserBooks',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'book_id', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'book_id', 'AttributeType': 'S'},
                {'AttributeName': 'rating', 'AttributeType': 'N'},
                {'AttributeName': 'date_added', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'BookRatingIndex',
                    'KeySchema': [
                        {'AttributeName': 'book_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'rating', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'UserDateIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'date_added', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        try:
            # Create Books table
            logger.info("Creating DigitalLibrary-Books table...")
            self.client.create_table(**books_table_config)
            logger.info("✅ DigitalLibrary-Books table created successfully")
            
            # Create UserBooks table  
            logger.info("Creating DigitalLibrary-UserBooks table...")
            self.client.create_table(**user_books_table_config)
            logger.info("✅ DigitalLibrary-UserBooks table created successfully")
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info("Tables already exist")
                return True
            else:
                logger.error(f"Error creating tables: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error creating tables: {e}")
            return False
    
    def get_books_table(self):
        """Get reference to books table"""
        return self.dynamodb.Table('DigitalLibrary-Books')
    
    def get_user_books_table(self):
        """Get reference to user-books table"""
        return self.dynamodb.Table('DigitalLibrary-UserBooks')
    
    def add_book(self, book_data: Dict[str, Any]) -> bool:
        """Add a book to the database"""
        try:
            table = self.get_books_table()
            
            # Ensure required fields
            if 'book_id' not in book_data:
                book_data['book_id'] = str(uuid.uuid4())
            
            if 'created_at' not in book_data:
                book_data['created_at'] = datetime.utcnow().isoformat()
            
            if 'updated_at' not in book_data:
                book_data['updated_at'] = datetime.utcnow().isoformat()
            
            table.put_item(Item=book_data)
            logger.info(f"✅ Book added: {book_data.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            return False
    
    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a book by its ID"""
        try:
            table = self.get_books_table()
            response = table.get_item(Key={'book_id': book_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting book {book_id}: {e}")
            return None
    
    def get_book_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get a book by its filename"""
        try:
            table = self.get_books_table()
            response = table.query(
                IndexName='FilenameIndex',
                KeyConditionExpression='filename = :filename',
                ExpressionAttributeValues={':filename': filename}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting book by filename {filename}: {e}")
            return None
    
    def get_all_books(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all books with pagination"""
        try:
            table = self.get_books_table()
            response = table.scan(Limit=limit)
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all books: {e}")
            return []
    
    def search_books_by_author(self, author: str) -> List[Dict[str, Any]]:
        """Search books by author"""
        try:
            table = self.get_books_table()
            response = table.query(
                IndexName='AuthorIndex',
                KeyConditionExpression='author = :author',
                ExpressionAttributeValues={':author': author}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error searching books by author {author}: {e}")
            return []
    
    def search_books_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Search books by genre"""
        try:
            table = self.get_books_table()
            response = table.query(
                IndexName='GenreIndex',
                KeyConditionExpression='genre = :genre',
                ExpressionAttributeValues={':genre': genre}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error searching books by genre {genre}: {e}")
            return []
    
    def update_book(self, book_id: str, update_data: Dict[str, Any]) -> bool:
        """Update book metadata"""
        try:
            table = self.get_books_table()
            
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in update_data.items():
                if key != 'book_id':  # Don't update the primary key
                    update_expression += f", {key} = :{key}"
                    expression_values[f':{key}'] = value
            
            table.update_item(
                Key={'book_id': book_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"✅ Book {book_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating book {book_id}: {e}")
            return False
    
    def delete_book(self, book_id: str) -> bool:
        """Delete a book from the database"""
        try:
            table = self.get_books_table()
            table.delete_item(Key={'book_id': book_id})
            logger.info(f"✅ Book {book_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting book {book_id}: {e}")
            return False
    
    # User-Book interaction methods
    def add_user_bookmark(self, user_id: str, book_id: str) -> bool:
        """Add a book to user's bookmarks"""
        try:
            table = self.get_user_books_table()
            table.put_item(Item={
                'user_id': user_id,
                'book_id': book_id,
                'bookmarked': True,
                'date_added': datetime.utcnow().isoformat()
            })
            logger.info(f"✅ Book {book_id} bookmarked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error bookmarking book {book_id} for user {user_id}: {e}")
            return False
    
    def remove_user_bookmark(self, user_id: str, book_id: str) -> bool:
        """Remove a book from user's bookmarks"""
        try:
            table = self.get_user_books_table()
            table.delete_item(Key={'user_id': user_id, 'book_id': book_id})
            logger.info(f"✅ Book {book_id} removed from bookmarks for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing bookmark {book_id} for user {user_id}: {e}")
            return False
    
    def get_user_bookmarks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bookmarks for a user"""
        try:
            table = self.get_user_books_table()
            response = table.query(
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='bookmarked = :bookmarked',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':bookmarked': True
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting bookmarks for user {user_id}: {e}")
            return []
    
    def add_user_rating(self, user_id: str, book_id: str, rating: int, review: str = "") -> bool:
        """Add or update user rating for a book"""
        try:
            table = self.get_user_books_table()
            table.put_item(Item={
                'user_id': user_id,
                'book_id': book_id,
                'rating': rating,
                'review': review,
                'date_rated': datetime.utcnow().isoformat()
            })
            logger.info(f"✅ Rating {rating} added for book {book_id} by user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding rating for book {book_id} by user {user_id}: {e}")
            return False

# Example usage and table creation
if __name__ == "__main__":
    # Initialize DynamoDB manager
    db_manager = DynamoDBManager()
    
    # Create tables
    print("Creating DynamoDB tables...")
    success = db_manager.create_tables()
    
    if success:
        print("✅ Tables created successfully!")
        
        # Example: Add a sample book
        sample_book = {
            'book_id': 'book-001',
            'filename': 'the-great-gatsby.pdf',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'genre': 'Fiction',
            'publication_year': 1925,
            'language': 'English',
            'description': 'A story of the fabulously wealthy Jay Gatsby...',
            'isbn': '9780743273565',
            'cover_url': 'https://example.com/cover.jpg',
            'file_size': 1024000,
            'tags': ['classic', 'american-literature', 'roaring-twenties']
        }
        
        db_manager.add_book(sample_book)
        print("✅ Sample book added!")
    else:
        print("❌ Failed to create tables")
