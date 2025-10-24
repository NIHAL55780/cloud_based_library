"""
Simple DynamoDB helper for your existing library
"""
import boto3
from botocore.exceptions import ClientError
import logging
from config import Config

logger = logging.getLogger(__name__)

class SimpleDynamoDBHelper:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=Config.DYNAMODB_REGION)
        self.books_table = self.dynamodb.Table(Config.DYNAMODB_BOOKS_TABLE)  # BookMetaData
        # Note: We'll only use the books table for now since you have one table
    
    def add_book(self, book_data):
        """Add a book to DynamoDB"""
        try:
            self.books_table.put_item(Item=book_data)
            logger.info(f"Book added: {book_data.get('title', 'Unknown')}")
            return True
        except ClientError as e:
            logger.error(f"Error adding book: {e}")
            return False
    
    def get_all_books(self):
        """Get all books from DynamoDB"""
        try:
            response = self.books_table.scan()
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting books: {e}")
            return []
    
    def get_book_by_filename(self, filename):
        """Get book by filename by parsing filename and matching with Title/Author"""
        try:
            logger.info(f"Searching for book with filename: {filename}")
            
            # Parse the filename to extract title and author
            parsed_data = self._parse_filename_to_title_author(filename)
            title = parsed_data.get('title')
            author = parsed_data.get('author')
            
            logger.info(f"Parsed filename - Title: '{title}', Author: '{author}'")
            
            # Build filter expression with simpler, more reliable matching
            filter_parts = []
            expression_values = {}
            
            if title:
                # Simple contains match for title
                filter_parts.append('contains(Title, :title)')
                expression_values[':title'] = title
                
                # Also try individual words from title
                title_words = title.split()
                for word in title_words:
                    if len(word) > 2:  # Only use words longer than 2 characters
                        filter_parts.append('contains(Title, :title_word)')
                        expression_values[':title_word'] = word
                        break  # Only use the first meaningful word
            
            if author:
                # Simple contains match for author
                filter_parts.append('contains(Author, :author)')
                expression_values[':author'] = author
                
                # Also try individual words from author
                author_words = author.split()
                for word in author_words:
                    if len(word) > 2:  # Only use words longer than 2 characters
                        filter_parts.append('contains(Author, :author_word)')
                        expression_values[':author_word'] = word
                        break  # Only use the first meaningful word
            
            if not filter_parts:
                logger.warning(f"Could not parse title or author from filename: {filename}")
                return None
            
            # Use OR logic for more flexible matching
            filter_expression = ' OR '.join(filter_parts)
            logger.info(f"Filter expression: {filter_expression}")
            logger.info(f"Expression values: {expression_values}")
            
            # Scan the table
            response = self.books_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values
            )
            items = response.get('Items', [])
            
            logger.info(f"Scan found {len(items)} items for filename: {filename}")
            
            if items:
                logger.info(f"Found book: {items[0].get('Title', 'Unknown')} by {items[0].get('Author', 'Unknown')}")
                return items[0]
            else:
                logger.warning(f"No book found with filename: {filename}")
                return None
            
        except ClientError as e:
            logger.error(f"Error getting book by filename: {e}")
            return None
    
    def _parse_filename_to_title_author(self, filename):
        """Parse filename to extract title and author with improved matching"""
        import re
        
        # Remove file extension
        name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
        
        logger.info(f"Parsing filename: '{name_without_ext}'")
        
        # Try different patterns in order of likelihood
        patterns = [
            # "Author by Title" pattern (most common)
            r'(.+?)\s+by\s+(.+)',
            # "Title - Author" pattern  
            r'(.+?)\s+-\s+(.+)',
            # "Author - Title" pattern
            r'(.+?)\s+-\s+(.+)',
            # "Author, Title" pattern
            r'(.+?),\s*(.+)',
            # "Title (Author)" pattern
            r'(.+?)\s+\((.+?)\)',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                part1, part2 = match.groups()
                part1 = part1.strip()
                part2 = part2.strip()
                
                logger.info(f"Pattern {i+1} matched: '{part1}' | '{part2}'")
                
                # Smart heuristic for determining which is title vs author
                if i == 0:  # "Author by Title" pattern
                    return {'title': part2, 'author': part1}
                elif i == 1:  # "Title - Author" pattern
                    return {'title': part1, 'author': part2}
                elif i == 2:  # "Author - Title" pattern  
                    return {'title': part2, 'author': part1}
                elif i == 3:  # "Author, Title" pattern
                    return {'title': part2, 'author': part1}
                elif i == 4:  # "Title (Author)" pattern
                    return {'title': part1, 'author': part2}
                else:
                    # Fallback: longer part is usually the title
                    if len(part1) > len(part2):
                        return {'title': part1, 'author': part2}
                    else:
                        return {'title': part2, 'author': part1}
        
        # If no pattern matches, try to extract just the title
        logger.info(f"No pattern matched, treating as title: '{name_without_ext}'")
        return {'title': name_without_ext.strip(), 'author': None}
    
    def get_book_by_id(self, book_id):
        """Get book by BookID (primary key)"""
        try:
            logger.info(f"Searching for book with BookID: {book_id}")
            
            # Use the correct primary key name: BookID
            response = self.books_table.get_item(Key={'BookID': book_id})
            item = response.get('Item')
            
            if item:
                logger.info(f"Found book: {item.get('title', 'Unknown')} by {item.get('author', 'Unknown')}")
                return item
            else:
                logger.warning(f"No book found with BookID: {book_id}")
                return None
            
        except ClientError as e:
            logger.error(f"Error getting book by BookID: {e}")
            return None
